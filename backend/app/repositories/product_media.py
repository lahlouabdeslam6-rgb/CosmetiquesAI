import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_product_media import AIProductMedia


class ProductMediaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: dict[str, Any]) -> AIProductMedia:
        requested_media = data.pop("requested_media")
        item = AIProductMedia(
            **data,
            requested_media_json=json.dumps(requested_media, ensure_ascii=False),
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def get(self, item_id: int) -> AIProductMedia | None:
        return await self.session.get(AIProductMedia, item_id)

    async def list(self, product_id: int | None = None, campaign_id: int | None = None) -> tuple[list[AIProductMedia], int]:
        conditions = []
        if product_id:
            conditions.append(AIProductMedia.product_id == product_id)
        if campaign_id:
            conditions.append(AIProductMedia.campaign_id == campaign_id)
        total = int(
            (
                await self.session.execute(
                    select(func.count(AIProductMedia.id)).where(*conditions)
                )
            ).scalar_one()
        )
        result = await self.session.execute(
            select(AIProductMedia)
            .where(*conditions)
            .order_by(AIProductMedia.updated_at.desc(), AIProductMedia.id.desc())
            .limit(100)
        )
        return list(result.scalars().all()), total

    async def update(self, item: AIProductMedia, data: dict[str, Any]) -> AIProductMedia:
        for field, value in data.items():
            setattr(item, field, value)
        item.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(item)
        return item
