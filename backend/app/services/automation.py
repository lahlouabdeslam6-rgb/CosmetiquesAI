from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.automation import AutomationRepository
from app.repositories.operations import OperationsRepository
from app.schemas.automation import (
    AutomationRunResponse,
    OrderAutomationResponse,
    OutboxCompleteResponse,
    OutboxItemResponse,
)
from app.schemas.commerce_workflow import CustomerFeedbackResponse
from app.repositories.order import OrderRepository
from app.services.commerce_workflow import CommerceWorkflowService
from app.services.delivery_agent import DeliveryAgentService
from app.services.order import OrderService


class AutomationService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        repository: AutomationRepository | None = None,
        operations: OperationsRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or AutomationRepository(session)
        self.operations = operations or OperationsRepository(session)

    async def scan_delivery(self) -> AutomationRunResponse:
        report = await DeliveryAgentService(self.session).report(notify=True)
        return AutomationRunResponse(
            scanned=report.summary.active_orders,
            notifications_created=report.summary.alerts_sent * 3,
            outbox_created=report.summary.alerts_sent * 2,
        )

    async def scan_abandoned_carts(
        self,
        *,
        older_than_hours: int = 24,
    ) -> AutomationRunResponse:
        carts = await self.repository.abandoned_carts(
            older_than=datetime.now(UTC) - timedelta(hours=older_than_hours)
        )
        notified = 0
        outbox_created = 0
        for user_id, email, _, quantity in carts:
            if await self.repository.event_logged_recently(
                action="automation.abandoned_cart_notified",
                entity_type="cart",
                entity_id=user_id,
                days=7,
            ):
                continue
            body = (
                f"Votre panier MIELMAR contient encore {quantity} article(s). "
                "Retrouvez-le depuis votre compte si vous souhaitez finaliser "
                "votre commande."
            )
            self.operations.add_notification(
                user_id=user_id,
                notification_type="abandoned_cart",
                title="Votre panier vous attend",
                message=body,
                link="/cart",
            )
            self.repository.add_outbox(
                event_type="abandoned_cart",
                channel="email",
                recipient=email,
                subject="Votre panier MIELMAR vous attend",
                body=body,
                reference_type="cart",
                reference_id=user_id,
            )
            self.operations.add_audit(
                actor_id=None,
                actor_role="automation",
                action="automation.abandoned_cart_notified",
                entity_type="cart",
                entity_id=user_id,
                details={"items": quantity, "channel": "email"},
            )
            notified += 1
            outbox_created += 1
        if notified:
            await self.session.commit()
        return AutomationRunResponse(
            scanned=len(carts),
            notifications_created=notified,
            outbox_created=outbox_created,
        )

    async def pending_outbox(self, limit: int) -> list[OutboxItemResponse]:
        return [
            OutboxItemResponse.model_validate(item)
            for item in await self.repository.pending_outbox(limit)
        ]

    async def complete_outbox(
        self,
        item_id: int,
        *,
        success: bool,
        error: str | None,
    ) -> OutboxCompleteResponse:
        item = await self.repository.complete_outbox(
            item_id,
            success=success,
            error=error,
        )
        if item is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Message d'automatisation introuvable",
            )
        return OutboxCompleteResponse(id=item.id, status=item.status)

    async def confirm_order(
        self,
        order_id: int,
        *,
        confirmed: bool,
        customer_message: str | None,
    ) -> OrderAutomationResponse:
        order = await OrderRepository(self.session).get_by_id(order_id)
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Commande introuvable")
        target_status = "confirmed" if confirmed else "cancelled"
        if order.order_status == target_status:
            return OrderAutomationResponse(
                order_id=order.id,
                order_status=order.order_status,
            )
        if order.order_status != "pending":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "La réponse de confirmation arrive après le traitement de la commande",
            )
        self.operations.add_audit(
            actor_id=None,
            actor_role="confirmation_agent",
            action="agent.confirmation.response_received",
            entity_type="order",
            entity_id=order_id,
            details={
                "confirmed": confirmed,
                "customer_message": customer_message,
            },
        )
        updated = await OrderService(self.session).update_admin_status(
            order_id,
            target_status,
            actor_id=None,
            actor_role="confirmation_agent",
        )
        return OrderAutomationResponse(
            order_id=updated.id,
            order_status=updated.order_status,
        )

    async def submit_feedback(
        self,
        order_id: int,
        *,
        rating: int,
        comment: str | None,
        source: str,
    ) -> CustomerFeedbackResponse:
        return await CommerceWorkflowService(self.session).record_feedback(
            order_id,
            rating=rating,
            comment=comment,
            source=source,
        )
