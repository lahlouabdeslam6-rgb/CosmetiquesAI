from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_roles
from app.db.sqlite import get_sqlite_session
from app.models.user import User
from app.repositories.operations import OperationsRepository
from app.schemas.product_media import (
    ProductMediaDraftUpdate,
    ProductMediaListResponse,
    ProductMediaPrepareRequest,
    ProductMediaResponse,
    ProductMediaResultRequest,
)
from app.services.product_media_agent import (
    ProductMediaAgentService,
    run_local_product_media_generation,
)


router = APIRouter(prefix="/admin/ai/product-media", tags=["Product Media Agent"])


@router.get("", response_model=ProductMediaListResponse)
async def list_product_media(
    _: Annotated[User, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_sqlite_session)],
    product_id: Annotated[int | None, Query(ge=1)] = None,
    campaign_id: Annotated[int | None, Query(ge=1)] = None,
) -> ProductMediaListResponse:
    return await ProductMediaAgentService(session).list(product_id, campaign_id)


@router.post("/prepare", response_model=ProductMediaResponse)
async def prepare_product_media(
    data: ProductMediaPrepareRequest,
    background_tasks: BackgroundTasks,
    admin: Annotated[User, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_sqlite_session)],
) -> ProductMediaResponse:
    result = await ProductMediaAgentService(session).prepare(data, admin.id)
    if result.status == "queued":
        background_tasks.add_task(run_local_product_media_generation, result.id)
    OperationsRepository(session).add_audit(
        actor_id=admin.id,
        actor_role=admin.role,
        action="ai.product_media.prepared",
        entity_type="ai_product_media",
        entity_id=result.id,
        details={"product_id": result.product_id, "media": result.requested_media},
    )
    await session.commit()
    return result


@router.patch("/{item_id}", response_model=ProductMediaResponse)
async def update_product_media_draft(
    item_id: int,
    data: ProductMediaDraftUpdate,
    admin: Annotated[User, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_sqlite_session)],
) -> ProductMediaResponse:
    result = await ProductMediaAgentService(session).update_draft(item_id, data)
    OperationsRepository(session).add_audit(
        actor_id=admin.id,
        actor_role=admin.role,
        action="ai.product_media.updated",
        entity_type="ai_product_media",
        entity_id=item_id,
        details={"fields": sorted(data.model_fields_set)},
    )
    await session.commit()
    return result


@router.post("/{item_id}/result", response_model=ProductMediaResponse)
async def register_product_media_result(
    item_id: int,
    data: ProductMediaResultRequest,
    admin: Annotated[User, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_sqlite_session)],
) -> ProductMediaResponse:
    result = await ProductMediaAgentService(session).register_result(item_id, data)
    OperationsRepository(session).add_audit(
        actor_id=admin.id,
        actor_role=admin.role,
        action="ai.product_media.result_received",
        entity_type="ai_product_media",
        entity_id=item_id,
        details={"provider": result.provider},
    )
    await session.commit()
    return result


@router.post("/{item_id}/approve", response_model=ProductMediaResponse)
async def approve_product_media(
    item_id: int,
    admin: Annotated[User, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_sqlite_session)],
) -> ProductMediaResponse:
    result = await ProductMediaAgentService(session).approve(item_id, admin.id)
    OperationsRepository(session).add_audit(
        actor_id=admin.id,
        actor_role=admin.role,
        action="ai.product_media.approved",
        entity_type="product",
        entity_id=result.product_id,
        details={"media_request_id": result.id},
    )
    await session.commit()
    return result
