"""Laboratory variants/chat and campaign-specific media.

Revision ID: 0021_agent_conversations_campaign_media
Revises: 0020_primary_admin
"""

from alembic import op
import sqlalchemy as sa


revision = "0021_agent_conversations_campaign_media"
down_revision = "0020_primary_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    request_columns = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("cosmetic_requests")
    }
    for name, column in {
        "formulas_json": sa.Column("formulas_json", sa.Text(), nullable=False, server_default="[]"),
        "conversation_json": sa.Column("conversation_json", sa.Text(), nullable=False, server_default="[]"),
        "selected_formula_index": sa.Column("selected_formula_index", sa.Integer(), nullable=False, server_default="0"),
    }.items():
        if name not in request_columns:
            op.add_column("cosmetic_requests", column)

    media_columns = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("ai_product_media")
    }
    for name, column in {
        "campaign_id": sa.Column("campaign_id", sa.Integer(), nullable=True),
        "platform": sa.Column("platform", sa.String(30), nullable=True),
        "placement": sa.Column("placement", sa.String(40), nullable=True),
    }.items():
        if name not in media_columns:
            op.add_column("ai_product_media", column)
    indexes = {
        index["name"]
        for index in sa.inspect(op.get_bind()).get_indexes("ai_product_media")
    }
    if "ix_ai_product_media_campaign_id" not in indexes:
        op.create_index("ix_ai_product_media_campaign_id", "ai_product_media", ["campaign_id"])
    if "ix_ai_product_media_platform" not in indexes:
        op.create_index("ix_ai_product_media_platform", "ai_product_media", ["platform"])


def downgrade() -> None:
    for name in ("ix_ai_product_media_platform", "ix_ai_product_media_campaign_id"):
        op.drop_index(name, table_name="ai_product_media")
    for name in ("placement", "platform", "campaign_id"):
        op.drop_column("ai_product_media", name)
    for name in ("selected_formula_index", "conversation_json", "formulas_json"):
        op.drop_column("cosmetic_requests", name)
