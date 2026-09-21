import pytest
from pydantic import ValidationError
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from app.main import app
from app.db.sqlite import Base
from app.models.site_setting import SiteSetting
from app.models.user import User
from app.models.operations import AuditLog
from app.api.site_navigation import read_navigation,write_navigation,NavigationWrite

@pytest.mark.asyncio
async def test_navigation_persists_order_and_label_without_changing_category_value():
    engine=create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as c: await c.run_sync(Base.metadata.create_all)
    Session=async_sessionmaker(engine,expire_on_commit=False)
    async with Session() as s:
        initial=await read_navigation(s)
        assert [c.value for c in initial.categories] == ["Épicerie", "Forme et bien-être", "Visage", "Corps", "Cheveux"]
        assert await s.scalar(select(func.count()).select_from(SiteSetting))==0
        user=User(email="test@example.test",role="admin",hashed_password="test-only")
        s.add(user);await s.commit()
        data=NavigationWrite(categories=[{"label":"Soins du visage","value":"Visage"},{"label":"Corps","value":"Corps"}])
        await write_navigation(data,user,s)
    async with Session() as s:
        saved=await read_navigation(s)
        assert saved.categories[0].label=="Soins du visage"
        assert saved.categories[0].value=="Visage"
        assert saved.categories[1].value=="Corps"
        assert await s.scalar(select(func.count()).select_from(AuditLog))==1
    await engine.dispose()

@pytest.mark.parametrize("categories",[[{"label":"   ","value":"Visage"}],[{"label":"Visage","value":"Visage"},{"label":"Autre","value":" visage "}]])
def test_navigation_rejects_empty_labels_and_duplicate_category_values(categories):
    with pytest.raises(ValidationError): NavigationWrite(categories=categories)

@pytest.mark.asyncio
@pytest.mark.parametrize("role",[None,"customer","support"])
async def test_navigation_only_admin_can_write(role):
    from app.core.security import get_current_user
    if role: app.dependency_overrides[get_current_user]=lambda:User(id=99,email="test@example.test",role=role,hashed_password="test-only")
    try:
        async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as client:
            r=await client.put("/api/site/navigation",json={"categories":[]})
        assert r.status_code in (401,403)
    finally: app.dependency_overrides.pop(get_current_user,None)
