"""Attach the curated MIELMAR catalogue image set to products that lack media."""

from datetime import UTC, datetime
from pathlib import Path

from pymongo import MongoClient

from app.core.config import settings


CATALOGUE_IMAGES = {
    2: "2-shampooing-douceur-miel-avoine.png",
    4: "4-shampooing-reparateur-argan-proteines.png",
    7: "7-masque-reparateur-karite-argan.png",
    9: "9-serum-pointes-seches-argan.png",
    12: "12-gel-nettoyant-aloe-miel.png",
    14: "14-brume-rose-hydratante.png",
    16: "16-serum-hydratation-aloe-hyaluronique.png",
    18: "18-creme-confort-miel-argan.png",
    22: "22-gel-douche-fleur-oranger.png",
    23: "23-savon-surgras-miel-argan.png",
    24: "24-lait-corps-argan-aloe.png",
    26: "26-gommage-corps-sucre-agrumes.png",
    30: "30-magnesium-vitamine-b6.png",
    31: "31-vitamine-d3.png",
    32: "32-vitamine-c-zinc.png",
    36: "36-spiruline-pure.png",
    38: "38-miel-oranger-maroc.png",
    39: "39-miel-argan.png",
    40: "40-amlou-amande-argan.png",
    41: "41-huile-argan-alimentaire.png",
    45: "45-miel-safran.png",
}


def main() -> None:
    client = MongoClient(settings.mongodb_url)
    products = client[settings.mongodb_database]["products"]
    updated = 0

    for product_id, filename in CATALOGUE_IMAGES.items():
        image_url = f"/static/uploads/products/catalog/{Path(filename).with_suffix('.webp').name}"
        result = products.update_one(
            {"product_id": product_id, "$or": [{"images": []}, {"images": {"$exists": False}}]},
            {"$set": {"images": [image_url], "updated_at": datetime.now(UTC)}},
        )
        updated += result.modified_count

    print(f"Catalogue images attached: {updated}/{len(CATALOGUE_IMAGES)}")


if __name__ == "__main__":
    main()
