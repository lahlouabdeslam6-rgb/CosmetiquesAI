"""Product Media Agent drafts and approvals.

Revision ID: 0016_product_media_agent
Revises: 0015_ai_commerce_workflow
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_product_media_agent"
down_revision = "0015_ai_commerce_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_product_media",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(length=240), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("visual_style", sa.String(length=120), nullable=False),
        sa.Column("requested_media_json", sa.Text(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("image_prompt", sa.Text(), nullable=True),
        sa.Column("video_prompt", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
        sa.Column("video_url", sa.String(length=1000), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "approved_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_product_media_product_id", "ai_product_media", ["product_id"])
    op.create_index("ix_ai_product_media_status", "ai_product_media", ["status"])
    op.create_index("ix_ai_product_media_created_by", "ai_product_media", ["created_by"])
    op.create_index("ix_ai_product_media_created_at", "ai_product_media", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_product_media_created_at", table_name="ai_product_media")
    op.drop_index("ix_ai_product_media_created_by", table_name="ai_product_media")
    op.drop_index("ix_ai_product_media_status", table_name="ai_product_media")
    op.drop_index("ix_ai_product_media_product_id", table_name="ai_product_media")
    op.drop_table("ai_product_media")
