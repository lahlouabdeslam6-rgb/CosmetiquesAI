from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.ai_marketing import AIMarketingCampaign
from app.models.order import Order
from app.services.commerce_workflow import CommerceWorkflowService


def make_order(status: str = "pending") -> Order:
    return Order(
        id=41,
        user_id=7,
        email="client@example.com",
        full_name="Client Mielmar",
        phone="+212600000000",
        address="10 rue Atlas",
        city="Casablanca",
        subtotal=320,
        delivery_fee=0,
        total=320,
        currency="MAD",
        order_status=status,
        payment_method="cash_on_delivery",
        payment_status="paid" if status == "delivered" else "pending",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_new_order_is_handed_to_confirmation_agent() -> None:
    automation = MagicMock()
    operations = MagicMock()
    service = CommerceWorkflowService(
        AsyncMock(),
        automation=automation,
        operations=operations,
    )

    service.on_order_created(make_order())

    call = automation.add_outbox.call_args.kwargs
    assert call["event_type"] == "order_confirmation"
    assert call["channel"] == "whatsapp"
    assert call["recipient"] == "+212600000000"
    operations.add_audit.assert_called_once()


@pytest.mark.asyncio
async def test_delivery_schedules_feedback_two_days_later() -> None:
    automation = MagicMock()
    operations = MagicMock()
    session = AsyncMock()
    service = CommerceWorkflowService(
        session,
        automation=automation,
        operations=operations,
    )
    before = datetime.now(UTC) + timedelta(days=2)

    await service.on_order_status_changed(
        make_order("delivered"),
        previous_status="shipped",
        actor_id=1,
        actor_role="admin",
    )

    call = automation.add_outbox.call_args.kwargs
    assert call["event_type"] == "feedback_request"
    assert call["channel"] == "whatsapp"
    assert call["scheduled_for"] >= before
    session.commit.assert_awaited_once()


def test_approved_marketing_campaign_is_queued_for_every_channel() -> None:
    automation = MagicMock()
    operations = MagicMock()
    service = CommerceWorkflowService(
        AsyncMock(),
        automation=automation,
        operations=operations,
    )
    campaign = AIMarketingCampaign(
        id=9,
        campaign_type="product_launch",
        topic="Nouveau soin",
        objective="Faire découvrir le produit",
        audience="clients MIELMAR",
        tone="premium",
        channels_json='["instagram", "facebook", "whatsapp"]',
        product_ids_json="[1]",
        selection_scores_json="[]",
        campaign_title="Lancement MIELMAR",
        headline="Votre nouveau soin",
        core_message="Découvrez le nouveau soin personnalisé de MIELMAR.",
        whatsapp_message="Découvrez le nouveau soin MIELMAR.",
        social_caption="Un nouveau soin arrive chez MIELMAR.",
        cta_label="Découvrir",
        hashtags_json='["#MIELMAR"]',
        status="approved",
        model="test",
        created_by=1,
        approved_by=1,
        approved_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    queued = service.queue_marketing_campaign(
        campaign,
        approved_by=1,
        pack_id=None,
    )

    assert queued == 3
    assert automation.add_outbox.call_count == 3
    assert {
        call.kwargs["channel"] for call in automation.add_outbox.call_args_list
    } == {"instagram", "facebook", "whatsapp"}
    operations.add_audit.assert_called_once()
