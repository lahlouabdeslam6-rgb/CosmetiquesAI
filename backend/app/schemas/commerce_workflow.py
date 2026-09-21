from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkflowStep(BaseModel):
    key: str
    agent: str
    label: str
    description: str


class WorkflowMessage(BaseModel):
    direction: str
    event_type: str
    channel: str
    body: str
    status: str
    scheduled_for: datetime | None = None
    processed_at: datetime | None = None


class WorkflowFeedbackDetail(BaseModel):
    rating: int
    comment: str | None
    source: str
    created_at: datetime


class WorkflowOrderItem(BaseModel):
    order_id: int
    customer_name: str
    phone: str
    order_status: str
    payment_status: str
    active_agent: str
    next_action: str
    confirmation_status: str
    delivery_status: str
    feedback_status: str
    messages: list[WorkflowMessage]
    feedback: WorkflowFeedbackDetail | None
    total: float
    currency: str
    created_at: datetime


class WorkflowSummary(BaseModel):
    active_orders: int
    awaiting_confirmation: int
    in_preparation: int
    in_delivery: int
    feedback_scheduled: int
    feedback_received: int
    pending_messages: int


class CommerceWorkflowReport(BaseModel):
    generated_at: datetime
    steps: list[WorkflowStep]
    summary: WorkflowSummary
    orders: list[WorkflowOrderItem]


class CustomerFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    rating: int
    comment: str | None
    source: str
    created_at: datetime
    updated_at: datetime
