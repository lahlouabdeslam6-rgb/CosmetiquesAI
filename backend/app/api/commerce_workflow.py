from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_roles
from app.db.sqlite import get_sqlite_session
from app.models.user import User
from app.schemas.commerce_workflow import CommerceWorkflowReport
from app.services.commerce_workflow import CommerceWorkflowService


router = APIRouter(prefix="/admin/ai/workflow", tags=["AI Commerce Workflow"])


@router.get("", response_model=CommerceWorkflowReport)
async def workflow_report(
    _: Annotated[User, Depends(require_roles("admin", "support"))],
    session: Annotated[AsyncSession, Depends(get_sqlite_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> CommerceWorkflowReport:
    return await CommerceWorkflowService(session).report(limit=limit)
