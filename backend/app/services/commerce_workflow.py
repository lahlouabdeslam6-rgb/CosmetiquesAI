from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
import json

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_marketing import AIMarketingCampaign
from app.models.automation import AutomationOutbox
from app.models.customer_feedback import CustomerFeedback
from app.models.order import Order
from app.models.operations import AuditLog
from app.repositories.automation import AutomationRepository
from app.repositories.operations import OperationsRepository
from app.schemas.commerce_workflow import (
    CommerceWorkflowReport,
    CustomerFeedbackResponse,
    WorkflowOrderItem,
    WorkflowStep,
    WorkflowSummary,
)


WORKFLOW_STEPS = [
    WorkflowStep(
        key="product",
        agent="Product, Media & Formulation Agents",
        label="Produit",
        description="Prépare la fiche, les médias ou la formule personnalisée avec validation admin.",
    ),
    WorkflowStep(
        key="content",
        agent="Content & SEO Agent",
        label="Contenu",
        description="Prépare les textes, mots-clés et contenus du catalogue.",
    ),
    WorkflowStep(
        key="marketing",
        agent="Marketing & Safety Agent",
        label="Lancement",
        description="Valide la campagne puis la place dans les canaux sélectionnés.",
    ),
    WorkflowStep(
        key="confirmation",
        agent="Confirmation Agent",
        label="Confirmation",
        description="Contacte le client sur WhatsApp et transmet sa réponse à la commande.",
    ),
    WorkflowStep(
        key="stock",
        agent="Stock Agent",
        label="Stock",
        description="Réserve les produits et suit séparément produits finis et matières premières.",
    ),
    WorkflowStep(
        key="delivery",
        agent="Delivery & Support Agent",
        label="Livraison",
        description="Suit le colis, détecte les retards et avertit le support.",
    ),
    WorkflowStep(
        key="feedback",
        agent="Feedback & Analytics Agent",
        label="Satisfaction",
        description="Demande un avis deux jours après livraison et alimente l'analyse.",
    ),
]


class CommerceWorkflowService:
    """Relie les agents métier par des événements fiables et traçables."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        operations: OperationsRepository | None = None,
        automation: AutomationRepository | None = None,
    ) -> None:
        self.session = session
        self.operations = operations or OperationsRepository(session)
        self.automation = automation or AutomationRepository(session)

    def on_order_created(self, order: Order) -> None:
        body = (
            f"Bonjour {order.full_name}, votre commande MIELMAR #{order.id} "
            f"de {order.total:.2f} {order.currency} est prête à être confirmée. "
            "Répondez OUI pour confirmer ou NON pour annuler."
        )
        self.automation.add_outbox(
            event_type="order_confirmation",
            channel="whatsapp",
            recipient=order.phone,
            body=body,
            reference_type="order",
            reference_id=order.id,
        )
        self.operations.add_audit(
            actor_id=None,
            actor_role="confirmation_agent",
            action="agent.confirmation.queued",
            entity_type="order",
            entity_id=order.id,
            details={"channel": "whatsapp", "next_status": "confirmed"},
        )

    async def on_order_status_changed(
        self,
        order: Order,
        *,
        previous_status: str,
        actor_id: int | None,
        actor_role: str,
    ) -> None:
        event_type: str | None = None
        body: str | None = None
        scheduled_for: datetime | None = None
        agent_role = "ai_orchestrator"

        if order.order_status == "confirmed":
            event_type = "order_confirmed"
            agent_role = "confirmation_agent"
            body = (
                f"Merci {order.full_name}. Votre commande MIELMAR #{order.id} "
                "est confirmée et passe à la préparation."
            )
        elif order.order_status == "preparing":
            agent_role = "stock_agent"
            self.operations.add_notification(
                target_role="admin",
                notification_type="stock_handoff",
                title=f"Commande #{order.id} en préparation",
                message="Le stock réservé est transmis à la préparation.",
                link=f"/admin?tab=orders&order={order.id}",
            )
        elif order.order_status == "shipped":
            event_type = "delivery_started"
            agent_role = "delivery_agent"
            body = (
                f"Votre commande MIELMAR #{order.id} est en livraison. "
                "Delivery Agent suit son avancement jusqu'à la réception."
            )
        elif order.order_status == "delivered":
            event_type = "feedback_request"
            agent_role = "feedback_agent"
            scheduled_for = datetime.now(UTC) + timedelta(days=2)
            body = (
                f"Bonjour {order.full_name}, deux jours se sont écoulés depuis "
                f"la livraison de la commande #{order.id}. Notez votre expérience "
                "de 1 à 5 et ajoutez un commentaire si vous le souhaitez."
            )
        elif order.order_status == "delivery_failed":
            event_type = "delivery_recovery"
            agent_role = "delivery_agent"
            body = (
                f"La livraison de votre commande MIELMAR #{order.id} n'a pas abouti. "
                "Répondez à ce message pour convenir d'un nouveau passage."
            )
            self.operations.add_notification(
                target_role="support",
                notification_type="delivery_failed",
                title=f"Livraison à reprendre #{order.id}",
                message="Delivery Agent demande une intervention du support.",
                link=f"/support?tab=orders&order={order.id}",
            )
        elif order.order_status == "cancelled":
            event_type = "order_cancelled"
            agent_role = "confirmation_agent"
            body = (
                f"Votre commande MIELMAR #{order.id} est annulée. "
                "Les quantités réservées ont été remises en stock."
            )

        if event_type and body:
            self.automation.add_outbox(
                event_type=event_type,
                channel="whatsapp",
                recipient=order.phone,
                body=body,
                reference_type="order",
                reference_id=order.id,
                scheduled_for=scheduled_for,
            )

        self.operations.add_audit(
            actor_id=actor_id,
            actor_role=agent_role,
            action=f"agent.workflow.{order.order_status}",
            entity_type="order",
            entity_id=order.id,
            details={
                "before": previous_status,
                "after": order.order_status,
                "triggered_by": actor_role,
                "message": event_type,
                "scheduled_for": scheduled_for.isoformat() if scheduled_for else None,
            },
        )
        await self.session.commit()

    def queue_marketing_campaign(
        self,
        campaign: AIMarketingCampaign,
        *,
        approved_by: int,
        pack_id: int | None,
    ) -> int:
        scheduled_for = campaign.starts_at or datetime.now(UTC)
        queued = 0
        hashtags = " ".join(campaign.hashtags)
        for channel in campaign.channels:
            if channel in {"instagram", "facebook", "tiktok", "x"}:
                body = "\n\n".join(
                    value for value in (campaign.social_caption, hashtags) if value
                )
                if channel == "x":
                    body = body[:280]
                recipient = f"mielmar:{channel}"
                subject = campaign.campaign_title
            elif channel == "email":
                body = campaign.email_body or campaign.core_message
                recipient = f"segment:{campaign.audience}"
                subject = campaign.email_subject or campaign.campaign_title
            else:
                body = campaign.whatsapp_message or campaign.core_message
                recipient = f"segment:{campaign.audience}"
                subject = None
            self.automation.add_outbox(
                event_type="marketing_campaign",
                channel=channel,
                recipient=recipient,
                subject=subject,
                body=body,
                reference_type="marketing_campaign",
                reference_id=campaign.id,
                scheduled_for=scheduled_for,
            )
            queued += 1
        self.operations.add_audit(
            actor_id=approved_by,
            actor_role="marketing_agent",
            action="agent.marketing.dispatch_queued",
            entity_type="ai_marketing_campaign",
            entity_id=campaign.id,
            details={
                "channels": campaign.channels,
                "messages": queued,
                "pack_id": pack_id,
                "scheduled_for": scheduled_for.isoformat(),
            },
        )
        return queued

    async def record_feedback(
        self,
        order_id: int,
        *,
        rating: int,
        comment: str | None,
        source: str,
    ) -> CustomerFeedbackResponse:
        order = await self.session.get(Order, order_id)
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Commande introuvable")
        if order.order_status != "delivered":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "L'avis peut être enregistré après la livraison",
            )
        result = await self.session.execute(
            select(CustomerFeedback).where(CustomerFeedback.order_id == order_id)
        )
        feedback = result.scalar_one_or_none()
        if feedback is None:
            feedback = CustomerFeedback(
                order_id=order_id,
                rating=rating,
                comment=comment,
                source=source,
            )
            self.session.add(feedback)
        else:
            feedback.rating = rating
            feedback.comment = comment
            feedback.source = source
            feedback.updated_at = datetime.now(UTC)
        self.operations.add_audit(
            actor_id=order.user_id,
            actor_role="feedback_agent",
            action="agent.feedback.received",
            entity_type="order",
            entity_id=order_id,
            details={"rating": rating, "source": source},
        )
        self.operations.add_notification(
            target_role="admin",
            notification_type="customer_feedback",
            title=f"Nouvel avis commande #{order_id}",
            message=f"Le client a donné une note de {rating}/5.",
            link="/admin?tab=commerce-workflow",
        )
        await self.session.commit()
        await self.session.refresh(feedback)
        return CustomerFeedbackResponse.model_validate(feedback)

    async def report(self, *, limit: int = 50) -> CommerceWorkflowReport:
        order_result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        orders = list(order_result.scalars().all())
        order_ids = [order.id for order in orders]
        feedback_by_order: dict[int, CustomerFeedback] = {}
        outbox_by_order: dict[int, list[AutomationOutbox]] = defaultdict(list)
        confirmation_replies: dict[int, AuditLog] = {}

        if order_ids:
            feedback_result = await self.session.execute(
                select(CustomerFeedback).where(CustomerFeedback.order_id.in_(order_ids))
            )
            feedback_by_order = {
                row.order_id: row for row in feedback_result.scalars().all()
            }
            outbox_result = await self.session.execute(
                select(AutomationOutbox).where(
                    AutomationOutbox.reference_type == "order",
                    AutomationOutbox.reference_id.in_([str(value) for value in order_ids]),
                )
            )
            for row in outbox_result.scalars().all():
                if row.reference_id and row.reference_id.isdigit():
                    outbox_by_order[int(row.reference_id)].append(row)
            reply_result = await self.session.execute(
                select(AuditLog).where(
                    AuditLog.entity_type == "order",
                    AuditLog.entity_id.in_([str(value) for value in order_ids]),
                    AuditLog.action == "agent.confirmation.response_received",
                ).order_by(AuditLog.created_at.desc())
            )
            for row in reply_result.scalars().all():
                if row.entity_id and row.entity_id.isdigit():
                    confirmation_replies.setdefault(int(row.entity_id), row)

        pending_messages = int(
            (
                await self.session.execute(
                    select(func.count(AutomationOutbox.id)).where(
                        AutomationOutbox.status == "pending"
                    )
                )
            ).scalar_one()
        )
        items = [
            self._workflow_item(
                order,
                outbox_by_order.get(order.id, []),
                feedback_by_order.get(order.id),
                confirmation_replies.get(order.id),
            )
            for order in orders
        ]
        return CommerceWorkflowReport(
            generated_at=datetime.now(UTC),
            steps=WORKFLOW_STEPS,
            summary=WorkflowSummary(
                active_orders=sum(
                    item.order_status not in {"delivered", "cancelled"} for item in items
                ),
                awaiting_confirmation=sum(item.order_status == "pending" for item in items),
                in_preparation=sum(
                    item.order_status in {"confirmed", "preparing"} for item in items
                ),
                in_delivery=sum(
                    item.order_status in {"shipped", "delivery_failed"} for item in items
                ),
                feedback_scheduled=sum(
                    item.feedback_status == "scheduled" for item in items
                ),
                feedback_received=len(feedback_by_order),
                pending_messages=pending_messages,
            ),
            orders=items,
        )

    @staticmethod
    def _workflow_item(
        order: Order,
        outbox: list[AutomationOutbox],
        feedback: CustomerFeedback | None,
        confirmation_reply: AuditLog | None,
    ) -> WorkflowOrderItem:
        events = {row.event_type: row for row in outbox}
        if order.order_status == "pending":
            active_agent = "Confirmation Agent"
            next_action = "Attendre la réponse WhatsApp du client"
        elif order.order_status in {"confirmed", "preparing"}:
            active_agent = "Stock Agent"
            next_action = "Préparer les produits réservés et lancer la livraison"
        elif order.order_status in {"shipped", "delivery_failed"}:
            active_agent = "Delivery & Support Agent"
            next_action = (
                "Reprogrammer la livraison avec le client"
                if order.order_status == "delivery_failed"
                else "Suivre le colis jusqu'à la réception"
            )
        elif order.order_status == "delivered":
            active_agent = "Feedback & Analytics Agent"
            next_action = "Avis reçu" if feedback else "Envoyer la demande d'avis à J+2"
        else:
            active_agent = "AI Orchestrator"
            next_action = "Parcours clôturé"

        confirmation = events.get("order_confirmation")
        delivery = events.get("delivery_started") or events.get("delivery_recovery")
        feedback_message = events.get("feedback_request")
        feedback_status = (
            "received"
            if feedback
            else "scheduled"
            if feedback_message
            else "not_due"
        )
        messages = [{
            "direction": "agent_to_client",
            "event_type": row.event_type,
            "channel": row.channel,
            "body": row.body,
            "status": row.status,
            "scheduled_for": row.scheduled_for,
            "processed_at": row.processed_at,
        } for row in sorted(outbox, key=lambda item: item.created_at)]
        if confirmation_reply:
            try:
                reply_details = json.loads(confirmation_reply.details or "{}")
            except (TypeError, ValueError):
                reply_details = {}
            messages.append({
                "direction": "client_to_agent",
                "event_type": "confirmation_response",
                "channel": "whatsapp",
                "body": reply_details.get("customer_message") or ("Commande confirmée" if reply_details.get("confirmed") else "Commande refusée"),
                "status": "received",
                "scheduled_for": None,
                "processed_at": confirmation_reply.created_at,
            })
        return WorkflowOrderItem(
            order_id=order.id,
            customer_name=order.full_name,
            phone=order.phone,
            order_status=order.order_status,
            payment_status=order.payment_status,
            active_agent=active_agent,
            next_action=next_action,
            confirmation_status=(
                "completed"
                if order.order_status != "pending"
                else confirmation.status if confirmation else "not_queued"
            ),
            delivery_status=(
                delivery.status
                if delivery
                else "completed"
                if order.order_status == "delivered"
                else "not_started"
            ),
            feedback_status=feedback_status,
            messages=messages,
            feedback={"rating": feedback.rating, "comment": feedback.comment, "source": feedback.source, "created_at": feedback.created_at} if feedback else None,
            total=order.total,
            currency=order.currency,
            created_at=order.created_at,
        )
