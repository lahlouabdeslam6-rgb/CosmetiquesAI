"""Opt-in local model acceptance check; creates unpublished versions of product 1."""
import asyncio
import json
from pathlib import Path

from app.db.mongodb import connect_mongodb, disconnect_mongodb
from app.db.sqlite import SqliteSession
from app.schemas.product_media import ProductMediaPrepareRequest
from app.services.product_media_agent import ProductMediaAgentService, run_local_product_media_generation
from app.services.media_plan import plan_media


async def main():
    await connect_mongodb()
    results = []
    parent_id = None
    cases = [
        {"image_description": "Fond blanc pur uni #ffffff, sans ombre ni reflet, produit centré, format carré. Garder exactement le sachet et son étiquette.", "video_description": "Même fond blanc et format carré. Zoom avant lent pendant 3 secondes."},
        {"image_description": "Fond orange uni #dd9933, sans ombre ni reflet. Produit plus grand, centré, format vertical 9:16. Conserver le vrai sachet et son étiquette.", "video_description": "Même fond orange et format vertical 9:16. Zoom arrière pendant 8 secondes.", "feedback": "Remplacer le blanc par orange, agrandir le produit et inverser le mouvement de caméra."},
    ]
    try:
        for index, case in enumerate(cases):
            async with SqliteSession() as session:
                service = ProductMediaAgentService(session)
                item = await service.prepare(ProductMediaPrepareRequest(product_id=1, parent_id=parent_id, **case), 1)
                print("CREATED", item.id, flush=True)
            await run_local_product_media_generation(item.id)
            async with SqliteSession() as session:
                result = await ProductMediaAgentService(session).get(item.id)
                record = {"id": result.id, "status": result.status, "error": result.error_message, "plan": result.render_plan, "image": result.image_url, "video": result.video_url}
                results.append(record)
                print(json.dumps(record, ensure_ascii=False), flush=True)
                if result.status != "review":
                    break
                expected_color = ("#ffffff", "#dd9933")[index]
                expected_duration = (3, 8)[index]
                assert result.render_plan["photo"]["background_color"] == expected_color
                assert result.render_plan["video"]["duration_seconds"] == expected_duration
                assert result.render_plan["video"]["motion"] == ("zoom_in", "zoom_out")[index]
                import imageio.v2 as imageio
                reader = imageio.get_reader(Path("app") / result.video_url.lstrip("/"))
                try:
                    assert abs(reader.get_meta_data()["duration"] - expected_duration) < 0.1
                finally:
                    reader.close()
                parent_id = result.id
        unsupported = await plan_media({"requested_media": ["video"], "video_description": "Rotation réelle à 360 degrés autour du produit pour voir le dos et les côtés."})
        print("UNSUPPORTED", unsupported.unsupported, flush=True)
        Path("data/media-acceptance.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    finally:
        await disconnect_mongodb()


if __name__ == "__main__":
    asyncio.run(main())
