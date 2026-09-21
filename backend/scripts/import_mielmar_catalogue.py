"""Import the reviewed MIELMAR catalogue as inactive, zero-stock drafts.

The command is a dry run by default. Pass --apply to write to MongoDB.
Existing MIELMAR records are matched by catalog_sku and are not reset.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import unicodedata
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.db.mongodb import connect_mongodb, disconnect_mongodb
from app.repositories.product import ProductRepository


DATA_PATH = Path(__file__).with_name("mielmar_catalogue.json")
DATASET_VERSION = "2026-09-14"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")[:180]


def parse_format(value: str) -> dict[str, float | str] | None:
    match = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*(ml|g|kg|l|gélules|comprimés|sachets)\s*", value, re.IGNORECASE)
    if not match:
        return None
    return {"count": float(match.group(1).replace(",", ".")), "unit": match.group(2).lower()}


def prepare(row: dict[str, Any]) -> dict[str, Any]:
    product_slug = slugify(f"mielmar-{row['name']}")
    ingredients = [
        {
            "name": item["name"],
            "form": None,
            "category": None,
            "amount_per_serving_mg": None,
            "is_proprietary_blend": False,
            "recommended_daily_mg": None,
            "upper_safety_limit_mg": None,
            "pubchem_cid": None,
            "molecular_formula": None,
            "molecular_weight": None,
            "inchikey": None,
            "canonical_smiles": None,
        }
        for item in row.get("ingredients", [])
        if item.get("name")
    ]
    description = str(row.get("description") or "").strip()
    usage = str(row.get("usage") or "").strip()
    seo_description = description[:180]
    tags = list(dict.fromkeys([row["category"], row["form_type"], usage]))[:12]
    return {
        "catalog_sku": row["sku"],
        "brand": "MIELMAR",
        "name": row["name"],
        "upc_barcode": None,
        "form_type": row["form_type"],
        "description": description,
        "category": row["category"],
        "price": float(row["price"]),
        "currency": "MAD",
        "stock": 0,
        "is_active": False,
        "images": [],
        "videos": [],
        "serving_size": parse_format(row.get("format", "")),
        "servings_per_container": 1,
        "ingredients": ingredients,
        "seo_title": row["name"][:70],
        "seo_description": seo_description,
        "seo_keywords": tags[:12],
        "tags": tags,
        "slug": product_slug,
        "image_alt": f"{row['name']} MIELMAR"[:180],
        "seo_faq": [],
        "source": {
            "url": "internal:mielmar-catalogue",
            "dataset_version": DATASET_VERSION,
        },
        "catalog_format": row.get("format"),
        "catalog_usage": usage,
        "catalog_source_ref": row.get("source_ref"),
        "catalog_notes": row.get("notes"),
    }


async def run(*, apply: bool) -> int:
    rows = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    prepared = [prepare(row) for row in rows]
    if len(prepared) != 44:
        raise RuntimeError(f"Expected 44 records, found {len(prepared)}")
    sku_counts = Counter(item["catalog_sku"] for item in prepared)
    duplicates = [sku for sku, count in sku_counts.items() if count > 1]
    if duplicates:
        raise RuntimeError(f"Duplicate SKUs: {duplicates}")

    await connect_mongodb()
    repository = ProductRepository()
    await repository.ensure_indexes()
    created = 0
    existing = 0
    try:
        for product in prepared:
            current = await repository.collection.find_one(
                {"catalog_sku": product["catalog_sku"]},
                {"_id": 0, "product_id": 1, "catalog_sku": 1},
            )
            if current:
                existing += 1
                continue
            if apply:
                await repository.create_product(product)
            created += 1
    finally:
        await disconnect_mongodb()

    mode = "APPLY" if apply else "DRY RUN"
    categories = Counter(item["category"] for item in prepared)
    print(f"{mode}: new={created} existing={existing} total={len(prepared)}")
    print("Categories: " + ", ".join(f"{name}={count}" for name, count in sorted(categories.items())))
    if not apply:
        print("No database changes were made. Run again with --apply to import drafts.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write missing drafts to MongoDB")
    args = parser.parse_args()
    return asyncio.run(run(apply=args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
