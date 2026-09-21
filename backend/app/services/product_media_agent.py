import asyncio
import json
from datetime import UTC, datetime

_MEDIA_JOB_LOCK = asyncio.Lock()

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_product_media import AIProductMedia
from app.repositories.product_media import ProductMediaRepository
from app.schemas.product_media import (
    ProductMediaDraftUpdate,
    ProductMediaListResponse,
    ProductMediaPrepareRequest,
    ProductMediaResponse,
    ProductMediaResultRequest,
)
from app.services.product import ProductService
from app.core.config import settings


class ProductMediaAgentService:
    def __init__(
        self,
        session: AsyncSession,
        repository: ProductMediaRepository | None = None,
        product_service: ProductService | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or ProductMediaRepository(session)
        self.products = product_service or ProductService()

    async def prepare(
        self, data: ProductMediaPrepareRequest, created_by: int
    ) -> ProductMediaResponse:
        product = await self.products.get_product(data.product_id)
        reference_images = [
            value
            for value in product.images
            if value.startswith("/static/") and "/ai/" not in value
        ]
        if settings.local_media_enabled and data.source_mode == "upload" and not reference_images:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Ajoutez une photo réelle du produit avant de générer ses médias",
            )
        name = (product.name or "Produit MIELMAR").strip()
        brand = (product.brand or "MIELMAR").strip()
        description = (product.description or "").strip()
        category = (product.category or "cosmétique").strip()
        details = data.instructions.strip() if data.instructions else ""
        image_details = data.image_description.strip() if data.image_description else ""
        video_details = data.video_description.strip() if data.video_description else ""
        parent = await self.get(data.parent_id) if data.parent_id else None
        if parent and parent.product_id != data.product_id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La version précédente appartient à un autre produit.")
        if parent and parent.status in {"queued", "planning", "generating"}:
            raise HTTPException(status.HTTP_409_CONFLICT, "Attendez la fin de cette version avant de la modifier.")
        source_url = parent.source_image_url if parent and parent.source_image_url else (reference_images[-1] if reference_images else None)
        request = {
            "product_name": name, "brand": brand, "product_description": description,
            "category": category, "visual_style": data.visual_style, "language": data.language,
            "requested_media": data.requested_media, "instructions": details,
            "image_description": image_details, "video_description": video_details,
            "feedback": data.feedback or "",
            "source_mode": data.source_mode,
            "campaign_id": data.campaign_id,
            "platform": data.platform,
            "placement": data.placement,
        }
        # Store raw descriptions, not contradictory hard-coded dark/gold briefs.
        image_prompt = image_details or f"Packshot de {name}, style {data.visual_style}." if "image" in data.requested_media else None
        video_prompt = video_details or f"Animation sobre de {name}, style {data.visual_style}." if "video" in data.requested_media else None
        stored_instructions = "\n".join(filter(None, [details, image_details, video_details, data.feedback]))

        item = await self.repository.create(
            {
                "product_id": data.product_id,
                "campaign_id": data.campaign_id,
                "platform": data.platform,
                "placement": data.placement,
                "product_name": name,
                "language": data.language,
                "visual_style": data.visual_style,
                "requested_media": list(dict.fromkeys(data.requested_media)),
                "instructions": stored_instructions or None,
                "image_prompt": image_prompt,
                "video_prompt": video_prompt,
                "status": "queued" if settings.local_media_enabled else "provider_required",
                "created_by": created_by,
                "source_image_url": source_url,
                "request_json": json.dumps(request, ensure_ascii=False),
                "parent_id": data.parent_id,
            }
        )
        await self.session.commit()
        return ProductMediaResponse.model_validate(item)

    async def list(self, product_id: int | None = None, campaign_id: int | None = None) -> ProductMediaListResponse:
        items, total = await self.repository.list(product_id, campaign_id)
        return ProductMediaListResponse(
            items=[ProductMediaResponse.model_validate(item) for item in items],
            total=total,
        )

    async def get(self, item_id: int) -> AIProductMedia:
        item = await self.repository.get(item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Demande média introuvable")
        return item

    async def update_draft(
        self, item_id: int, data: ProductMediaDraftUpdate
    ) -> ProductMediaResponse:
        item = await self.get(item_id)
        if item.status in {"queued", "planning", "generating"}:
            raise HTTPException(status.HTTP_409_CONFLICT, "Cette version est en cours de génération.")
        values = data.model_dump(exclude_unset=True)
        if not values:
            return ProductMediaResponse.model_validate(item)
        values.update({"status": "provider_required", "error_message": None})
        item = await self.repository.update(item, values)
        await self.session.commit()
        return ProductMediaResponse.model_validate(item)
    async def register_result(
        self, item_id: int, data: ProductMediaResultRequest
    ) -> ProductMediaResponse:
        item = await self.get(item_id)
        requested = set(item.requested_media)
        if "image" in requested and not data.image_url:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La photo générée est requise")
        if "video" in requested and not data.video_url:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La vidéo générée est requise")
        item = await self.repository.update(
            item,
            {
                "provider": data.provider,
                "image_url": data.image_url,
                "video_url": data.video_url,
                "status": "review",
                "error_message": None,
            },
        )
        await self.session.commit()
        return ProductMediaResponse.model_validate(item)

    async def approve(self, item_id: int, approved_by: int) -> ProductMediaResponse:
        item = await self.get(item_id)
        if item.status != "review":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Le média doit être généré et vérifié avant validation",
            )
        product = await self.products.get_product(item.product_id)
        if item.image_url and item.image_url not in product.images:
            await self.products.add_image(item.product_id, item.image_url)
        if item.video_url and item.video_url not in product.videos:
            await self.products.repository.set_videos(
                item.product_id, [*product.videos, item.video_url]
            )
        now = datetime.now(UTC)
        item = await self.repository.update(
            item,
            {"status": "approved", "approved_by": approved_by, "approved_at": now},
        )
        await self.session.commit()
        return ProductMediaResponse.model_validate(item)


async def run_local_product_media_generation(item_id: int) -> None:
    from anyio import to_thread
    from app.db.sqlite import SqliteSession
    from app.services.local_media import generate_local_product_media
    from app.services.media_plan import plan_media

    # CPU/RAM-heavy local models run one job at a time; queued jobs remain visible.
    async with _MEDIA_JOB_LOCK, SqliteSession() as session:
        service = ProductMediaAgentService(session)
        item = await service.get(item_id)
        if item.status != "queued":
            return
        try:
            await service.repository.update(item, {"status": "planning", "error_message": None})
            await session.commit()
            parent = await service.get(item.parent_id) if item.parent_id else None
            request = item.request_spec or {
                "product_name": item.product_name, "image_description": item.image_prompt,
                "video_description": item.video_prompt, "instructions": item.instructions,
                "requested_media": item.requested_media,
            }
            plan = await plan_media(request, parent.render_plan if parent else None)
            await service.repository.update(item, {"plan_json": plan.model_dump_json()})
            if plan.unsupported:
                await service.repository.update(item, {
                    "status": "needs_changes",
                    "error_message": "Consignes non réalisables par le moteur local : " + "; ".join(plan.unsupported),
                })
                await session.commit()
                return
            await service.repository.update(item, {"status": "generating"})
            await session.commit()
            image_url, video_url = await to_thread.run_sync(
                generate_local_product_media, plan, item.requested_media, item.source_image_url,
                request.get("source_mode", "upload"), request.get("product_name", item.product_name),
                request.get("brand", "MIELMAR"), request.get("category", "cosmétique"),
                " ".join(filter(None, [request.get("product_description", ""), request.get("image_description", "")])),
            )
            await service.register_result(item_id, ProductMediaResultRequest(
                provider="Ollama local · détourage · composition 2D",
                image_url=image_url, video_url=video_url,
            ))
        except Exception as error:
            await session.rollback()
            item = await service.get(item_id)
            await service.repository.update(item, {"status": "failed", "error_message": str(error)[:800]})
            await session.commit()
