import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.ai_product_media import AIProductMedia
from app.schemas.product import ProductResponse
from app.schemas.product_media import ProductMediaPrepareRequest
from app.services.product_media_agent import ProductMediaAgentService


@pytest.mark.asyncio
async def test_media_agent_preserves_descriptions_and_original_reference() -> None:
    session = AsyncMock()
    repository = AsyncMock()
    products = MagicMock()
    products.get_product = AsyncMock(
        return_value=ProductResponse(
            product_id=12,
            name="Sérum éclat",
            brand="MIELMAR",
            category="Visage",
            description="Soin hydratant validé.",
            price=190,
            images=["/static/uploads/products/serum-reference.webp"],
            videos=[],
        )
    )

    async def create(data: dict) -> AIProductMedia:
        now = datetime.now(UTC)
        return AIProductMedia(
            id=5,
            product_id=data["product_id"],
            product_name=data["product_name"],
            language=data["language"],
            visual_style=data["visual_style"],
            requested_media_json=json.dumps(data["requested_media"]),
            instructions=data["instructions"],
            image_prompt=data["image_prompt"],
            video_prompt=data["video_prompt"],
            request_json=data["request_json"],
            source_image_url=data["source_image_url"],
            status=data["status"],
            created_by=data["created_by"],
            created_at=now,
            updated_at=now,
        )

    repository.create.side_effect = create
    service = ProductMediaAgentService(session, repository, products)

    result = await service.prepare(
        ProductMediaPrepareRequest(
            product_id=12,
            source_mode="upload",
            language="fr",
            visual_style="premium naturel",
            requested_media=["image", "video"],
            image_description="Flacon seul sur fond sombre",
            video_description="Rotation lente du flacon",
        ),
        created_by=3,
    )

    assert result.status == "queued"
    assert result.image_prompt == "Flacon seul sur fond sombre"
    assert result.video_prompt == "Rotation lente du flacon"
    assert result.request_spec["product_name"] == "Sérum éclat"
    assert result.request_spec["image_description"] == result.image_prompt
    assert result.request_spec["video_description"] == result.video_prompt
    assert result.source_image_url == "/static/uploads/products/serum-reference.webp"
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_media_agent_can_create_original_packaging_without_reference() -> None:
    session = AsyncMock()
    repository = AsyncMock()
    products = MagicMock()
    products.get_product = AsyncMock(return_value=ProductResponse(
        product_id=13, name="Crème sur mesure", brand="MIELMAR", category="Cosmétique",
        description="Formule validée", price=0, images=[], videos=[],
    ))

    async def create(data: dict) -> AIProductMedia:
        now = datetime.now(UTC)
        return AIProductMedia(id=6, product_id=data["product_id"], product_name=data["product_name"],
            language=data["language"], visual_style=data["visual_style"],
            requested_media_json=json.dumps(data["requested_media"]), instructions=data["instructions"],
            image_prompt=data["image_prompt"], video_prompt=data["video_prompt"], request_json=data["request_json"],
            source_image_url=data["source_image_url"], status=data["status"], created_by=data["created_by"],
            created_at=now, updated_at=now)

    repository.create.side_effect = create
    result = await ProductMediaAgentService(session, repository, products).prepare(
        ProductMediaPrepareRequest(product_id=13, source_mode="agent", requested_media=["image"]), 3,
    )
    assert result.status == "queued"
    assert result.source_image_url is None
    assert result.request_spec["source_mode"] == "agent"


@pytest.mark.asyncio
async def test_revision_cannot_use_another_products_plan():
    from fastapi import HTTPException
    products = MagicMock()
    products.get_product = AsyncMock(return_value=ProductResponse(
        product_id=12, name="Sérum", price=100, images=["/static/uploads/products/original.png"], videos=[],
    ))
    repository = AsyncMock()
    repository.get.return_value = AIProductMedia(id=7, product_id=99, status="review")
    with pytest.raises(HTTPException) as exc:
        await ProductMediaAgentService(AsyncMock(), repository, products).prepare(
            ProductMediaPrepareRequest(product_id=12, parent_id=7), 1,
        )
    assert exc.value.status_code == 422
    repository.create.assert_not_awaited()
