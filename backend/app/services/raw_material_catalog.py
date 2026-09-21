"""Import user-supplied reference data without inventing or replacing inventory."""
import asyncio
import hashlib
import json
import unicodedata
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cosmetic_formulation import RawMaterial
from app.models.site_setting import SiteSetting

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data/raw_material_catalog.json"

def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

def normalized_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()

def catalog_metadata(row: RawMaterial) -> dict:
    try:
        return json.loads(row.catalog_json or "{}")
    except (ValueError, TypeError):
        return {}

async def import_catalog(session: AsyncSession) -> dict:
    catalog = load_catalog()
    existing = (await session.scalars(select(RawMaterial))).all()
    by_name = {normalized_name(row.name): row for row in existing}
    categories = {group["id"]: group["name"] for group in catalog["categories"]}
    result = {"created": 0, "enriched": 0, "unchanged": 0, "total_source": len(catalog["materials"])}
    for item in catalog["materials"]:
        key = normalized_name(item["name"])
        row = by_name.get(key)
        if row and catalog_metadata(row).get("catalog_version") == catalog["version"]:
            result["unchanged"] += 1
            continue
        metadata = {**item, "category_ids": item["categories"], "categories": [categories[c] for c in item["categories"]], "catalog_version": catalog["version"]}
        if row:
            # Preserve every inventory field, ID, and any administrator metadata.
            previous = catalog_metadata(row)
            metadata["stock_recorded"] = previous.get("stock_recorded", True)
            row.catalog_json = json.dumps({**previous, **metadata}, ensure_ascii=False)
            result["enriched"] += 1
        else:
            reference = "MP-" + hashlib.sha256(key.encode()).hexdigest()[:10].upper()
            row = RawMaterial(name=item["name"], reference=reference, unit="g", quantity=0,
                reserved_quantity=0, minimum_quantity=0, is_active=True,
                catalog_json=json.dumps(metadata, ensure_ascii=False))
            session.add(row)
            by_name[key] = row
            result["created"] += 1
    setting = await session.get(SiteSetting, "raw_material_catalog_import")
    if not setting:
        session.add(SiteSetting(key="raw_material_catalog_import", value={"version":catalog["version"], **result}))
    await session.commit()
    return result

async def main():
    from app.db.sqlite import SqliteSession
    async with SqliteSession() as session:
        print(json.dumps(await import_catalog(session)))

if __name__ == "__main__":
    asyncio.run(main())
