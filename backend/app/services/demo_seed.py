from __future__ import annotations

import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.sqlite import SqliteSession
from app.models.user import User
from app.repositories.product import ProductRepository


CATALOGUE_PATH = Path("scripts/mielmar_catalogue.json")
SELECTED_SKUS = {
    "MIE-CH-001", "MIE-CH-003", "MIE-CH-006", "MIE-CH-008",
    "MIE-VI-001", "MIE-VI-003", "MIE-VI-005", "MIE-VI-007",
    "MIE-CO-001", "MIE-CO-002", "MIE-CO-003", "MIE-CO-005",
    "MIE-FB-001", "MIE-FB-002", "MIE-FB-003", "MIE-FB-007",
    "MIE-EP-001", "MIE-EP-002", "MIE-EP-003", "MIE-EP-004",
}
IMAGE_NAMES = {
    path.name.split("-", 1)[1]: path.name
    for path in Path("app/static/uploads/products/catalog").glob("*.webp")
}


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")[:180]


def _image_for(name: str) -> str | None:
    slug = _slug(name)
    match = next((filename for key, filename in IMAGE_NAMES.items() if slug in key), None)
    return f"/static/uploads/products/catalog/{match}" if match else None


async def seed_demo_data() -> None:
    """Create a repeatable, non-sensitive catalogue and admin for free demo hosting."""
    repository = ProductRepository()
    if await repository.collection.count_documents({}) == 0 and CATALOGUE_PATH.exists():
        now = datetime.now(UTC)
        rows = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
        products = []
        for product_id, row in enumerate(rows, 2):
            image = _image_for(row["name"])
            products.append({
                "product_id": product_id,
                "catalog_sku": row["sku"],
                "brand": "MIELMAR",
                "name": row["name"],
                "upc_barcode": None,
                "form_type": row["form_type"],
                "description": row.get("description") or "",
                "category": row["category"],
                "price": float(row["price"]),
                "currency": "MAD",
                "stock": 100,
                "is_active": row["sku"] in SELECTED_SKUS,
                "launch_selection": row["sku"] in SELECTED_SKUS,
                "images": [image] if image else [],
                "videos": [],
                "ingredients": [
                    {"name": item["name"], "form": None, "category": None,
                     "amount_per_serving_mg": None, "is_proprietary_blend": False,
                     "recommended_daily_mg": None, "upper_safety_limit_mg": None,
                     "pubchem_cid": None, "molecular_formula": None,
                     "molecular_weight": None, "inchikey": None,
                     "canonical_smiles": None}
                    for item in row.get("ingredients", []) if item.get("name")
                ],
                "serving_size": None,
                "servings_per_container": 1,
                "seo_title": row["name"][:70],
                "seo_description": str(row.get("description") or "")[:180],
                "seo_keywords": [row["category"], row["form_type"]],
                "seo_faq": [],
                "tags": [row["category"], row["form_type"]],
                "slug": _slug(f"mielmar-{row['name']}"),
                "image_alt": f"{row['name']} MIELMAR"[:180],
                "created_at": now,
                "updated_at": now,
            })
        if products:
            await repository.collection.insert_many(products)
            await repository.ensure_indexes()

    email = settings.demo_admin_email.strip().lower()
    password = settings.demo_admin_password
    if email and len(password) >= 8:
        async with SqliteSession() as session:
            existing = await session.scalar(select(User).where(User.email == email))
            if existing is None:
                session.add(User(
                    email=email,
                    full_name=settings.demo_admin_name,
                    hashed_password=hash_password(password),
                    role="admin",
                    is_super_admin=True,
                    is_active=True,
                    is_email_verified=True,
                ))
                await session.commit()
