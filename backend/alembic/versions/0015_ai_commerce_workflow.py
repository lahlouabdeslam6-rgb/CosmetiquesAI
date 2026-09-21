"""AI commerce workflow and scheduled feedback.

Revision ID: 0015_ai_commerce_workflow
Revises: 0014_cosmetic_formulation
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_ai_commerce_workflow"
down_revision = "0014_cosmetic_formulation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "automation_outbox",
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE automation_outbox SET scheduled_for = created_at "
        "WHERE scheduled_for IS NULL"
    )
    op.create_index(
        "ix_automation_outbox_scheduled_for",
        "automation_outbox",
        ["scheduled_for"],
    )
    op.create_table(
        "customer_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer(),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_customer_feedback_order_id", "customer_feedback", ["order_id"], unique=True
    )
    op.create_index(
        "ix_customer_feedback_created_at", "customer_feedback", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_customer_feedback_created_at", table_name="customer_feedback")
    op.drop_index("ix_customer_feedback_order_id", table_name="customer_feedback")
    op.drop_table("customer_feedback")
    op.drop_index("ix_automation_outbox_scheduled_for", table_name="automation_outbox")
    op.drop_column("automation_outbox", "scheduled_for")
