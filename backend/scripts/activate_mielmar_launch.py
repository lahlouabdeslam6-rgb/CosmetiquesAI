"""Activate only the approved MIELMAR launch selection."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.db.mongodb import connect_mongodb, disconnect_mongodb
from app.repositories.product import ProductRepository


SELECTED_SKUS = [
    "MIE-CH-001", "MIE-CH-003", "MIE-CH-006", "MIE-CH-008",
    "MIE-VI-001", "MIE-VI-003", "MIE-VI-005", "MIE-VI-007",
    "MIE-CO-001", "MIE-CO-002", "MIE-CO-003", "MIE-CO-005",
    "MIE-FB-001", "MIE-FB-002", "MIE-FB-003", "MIE-FB-007",
    "MIE-EP-001", "MIE-EP-002", "MIE-EP-003", "MIE-EP-004",
]


async def main() -> int:
    await connect_mongodb()
    repository = ProductRepository()
    try:
        now = datetime.now(UTC)
        selected = await repository.collection.update_many(
            {"brand": "MIELMAR", "catalog_sku": {"$in": SELECTED_SKUS}},
            {"$set": {"is_active": True, "launch_selection": True, "updated_at": now}},
        )
        phase_two = await repository.collection.update_many(
            {"brand": "MIELMAR", "catalog_sku": {"$nin": SELECTED_SKUS}},
            {"$set": {"is_active": False, "launch_selection": False, "updated_at": now}},
        )
        active_count = await repository.collection.count_documents(
            {"brand": "MIELMAR", "is_active": True}
        )
        missing = await repository.collection.count_documents(
            {"catalog_sku": {"$in": SELECTED_SKUS}}
        )
        if missing != len(SELECTED_SKUS):
            raise RuntimeError(f"Expected {len(SELECTED_SKUS)} selected products, found {missing}")
        print(
            f"selected_matched={selected.matched_count} "
            f"phase_two_matched={phase_two.matched_count} active_mielmar={active_count}"
        )
    finally:
        await disconnect_mongodb()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
