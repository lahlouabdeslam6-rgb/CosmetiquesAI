"""Rubriques publiques et configuration réservée à l'administration."""
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlite import get_sqlite_session
from app.core.security import require_roles
from app.models.user import User
from app.models.operations import AuditLog
from app.models.site_setting import SiteSetting

router = APIRouter(prefix="/site", tags=["Navigation boutique"])
DEFAULT_CATEGORIES = ["Épicerie", "Forme et bien-être", "Visage", "Corps", "Cheveux"]

class CategoryEntry(BaseModel):
    label: str = Field(min_length=1,max_length=80)
    value: str = Field(min_length=1,max_length=120)

    @field_validator("label", "value")
    @classmethod
    def meaningful_text(cls, value):
        value=value.strip()
        if not value:
            raise ValueError("Le nom ne peut pas être vide")
        return value

class NavigationWrite(BaseModel):
    categories: list[CategoryEntry] = Field(max_length=60)

    @field_validator("categories")
    @classmethod
    def unique_categories(cls, categories):
        values=[c.value.casefold() for c in categories]
        if len(set(values)) != len(values):
            raise ValueError("Chaque catégorie doit avoir une valeur catalogue unique")
        return categories

@router.get("/navigation", response_model=NavigationWrite)
async def read_navigation(session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    row=await session.get(SiteSetting,"navigation")
    if row:
        return NavigationWrite.model_validate(row.value)
    return NavigationWrite(categories=[CategoryEntry(label=c,value=c) for c in DEFAULT_CATEGORIES])

@router.put("/navigation", response_model=NavigationWrite)
async def write_navigation(data: NavigationWrite, user: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    row=await session.get(SiteSetting,"navigation")
    if row is None:
        row=SiteSetting(key="navigation",value=data.model_dump())
        session.add(row)
    else:
        row.value=data.model_dump()
    session.add(AuditLog(actor_id=user.id,actor_role=user.role,action="site_navigation_updated",entity_type="site_setting",entity_id="navigation",details="Modification manuelle des rubriques du catalogue"))
    await session.commit()
    return data
