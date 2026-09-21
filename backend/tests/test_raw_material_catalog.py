import json

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.cosmetic_formulation import MaterialPatch, material_dict, update_raw_material
from app.db.sqlite import Base
from app.models.cosmetic_formulation import RawMaterial
from app.models.user import User
from app.services.raw_material_catalog import catalog_metadata, import_catalog, load_catalog, normalized_name


def test_catalog_merges_sources_and_retains_reference_data():
    data = load_catalog()
    items = data['materials']
    keys = [normalized_name(x['name']) for x in items]
    assert len(keys) == len(set(keys)) == 260
    assert len(data['categories']) == 21
    assert len(data['essentials']) == 50
    assert len(data['pdf_product_guides']) == 8
    glycerin = next(x for x in items if x['name'] == 'Glycerin')
    assert any('Texte' in x['source'] for x in glycerin['source_records'])
    assert any(x.get('page') == 2 for x in glycerin['source_records'])
    assert len(glycerin['dosage_references']) >= 2
    assert all(x['stock_recorded'] is False for x in items)
    assert all(x['categories'] for x in items)


@pytest.mark.asyncio
async def test_import_is_idempotent_preserves_stock_and_distinguishes_unknown_from_zero():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        admin = User(email='catalog-admin@example.test', role='admin', hashed_password='test-only')
        existing = RawMaterial(name='Glycerin', reference='SUP-17', unit='kg', quantity=12,
            reserved_quantity=2, minimum_quantity=3, cost_per_unit=42, supplier='Existing supplier', is_active=False)
        session.add_all([admin, existing])
        await session.commit()
        existing_id = existing.id
        result = await import_catalog(session)
        assert result['created'] == 259 and result['enriched'] == 1
        assert existing.id == existing_id
        assert (existing.reference, existing.unit, existing.quantity, existing.reserved_quantity,
                existing.minimum_quantity, existing.cost_per_unit, existing.supplier, existing.is_active) == (
                'SUP-17', 'kg', 12, 2, 3, 42, 'Existing supplier', False)
        assert material_dict(existing)['stock_status'] == 'healthy'
        aqua = await session.scalar(select(RawMaterial).where(RawMaterial.name == 'Aqua'))
        assert material_dict(aqua)['stock_status'] == 'unrecorded'
        assert material_dict(aqua)['available_quantity'] == 0
        await update_raw_material(aqua.id, MaterialPatch(supplier='New supplier'), admin, session)
        assert material_dict(aqua)['stock_status'] == 'unrecorded'
        await update_raw_material(aqua.id, MaterialPatch(quantity=0), admin, session)
        assert material_dict(aqua)['stock_status'] == 'low'
        again = await import_catalog(session)
        assert again['created'] == 0 and again['unchanged'] == 260
        assert catalog_metadata(aqua)['stock_recorded'] is True
        assert await session.scalar(select(func.count()).select_from(RawMaterial)) == 260
        with pytest.raises(HTTPException) as exc:
            await update_raw_material(existing.id, MaterialPatch(quantity=1), admin, session)
        assert exc.value.status_code == 422
        assert existing.quantity == 12
        with pytest.raises(HTTPException):
            await update_raw_material(existing.id, MaterialPatch(quantity=None), admin, session)
    await engine.dispose()
