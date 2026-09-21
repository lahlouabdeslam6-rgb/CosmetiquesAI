"""Create storefront-ready WebP files and switch catalogue products to them."""

from datetime import UTC, datetime
from pathlib import Path

from PIL import Image
from pymongo import MongoClient

from app.core.config import settings


CATALOGUE_DIR = Path("/app/app/static/uploads/products/catalog")
MAX_EDGE = 1200


def main() -> None:
    client = MongoClient(settings.mongodb_url)
    products = client[settings.mongodb_database]["products"]
    converted = 0

    for source in sorted(CATALOGUE_DIR.glob("*.png")):
        product_id = int(source.stem.split("-", 1)[0])
        target = source.with_suffix(".webp")
        with Image.open(source) as image:
            image = image.convert("RGB")
            image.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
            image.save(target, "WEBP", quality=88, method=6)

        image_url = f"/static/uploads/products/catalog/{target.name}"
        products.update_one(
            {"product_id": product_id},
            {"$set": {"images": [image_url], "updated_at": datetime.now(UTC)}},
        )
        converted += 1

    print(f"Catalogue images optimized: {converted}")


if __name__ == "__main__":
    main()
