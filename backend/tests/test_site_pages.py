import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.db.sqlite import Base
from app.models.user import User
from app.models.site_page import SitePage
from app.models.operations import AuditLog
from app.api.site import read_page, update_page, PageWrite

@pytest.mark.asyncio
async def test_site_page_write_requires_authentication():
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as client:
        response=await client.put("/api/site/pages/laboratoire",json={"title":"Test","body":"Texte"})
    assert response.status_code in (401,403)

@pytest.mark.asyncio
async def test_editorial_pages_persist_and_audit_without_seeding():
    engine=create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    Session=async_sessionmaker(engine,expire_on_commit=False)
    async with Session() as session:
        initial=await read_page("laboratoire",session)
        assert initial["body"]==""
        assert await session.scalar(select(func.count()).select_from(SitePage))==0
        user=User(email="admin@example.test",role="admin",hashed_password="isolated-test-only")
        session.add(user);await session.commit()
        await update_page("laboratoire",PageWrite(title="Notre laboratoire",body="Texte validé."),user,session)
    async with Session() as session:
        assert (await read_page("laboratoire",session))["body"]=="Texte validé."
        assert await session.scalar(select(func.count()).select_from(AuditLog))==1
    await engine.dispose()

@pytest.mark.asyncio
async def test_unknown_site_page_is_not_created():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as error:
        await read_page("inconnue",None)
    assert error.value.status_code==404

@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["customer", "support"])
async def test_site_page_write_denies_non_admin_roles(role):
    from app.core.security import get_current_user
    app.dependency_overrides[get_current_user] = lambda: User(id=999, email="isolated@example.test",role=role,hashed_password="test-only")
    try:
        async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as client:
            response=await client.put("/api/site/pages/laboratoire",json={"title":"Test","body":"Texte"})
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)