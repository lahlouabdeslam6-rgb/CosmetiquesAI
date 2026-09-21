"""Persist original reference, requests and executed media plans for revisions."""
from alembic import op
import sqlalchemy as sa

revision = "0017_media_description_plans"
down_revision = "0016_product_media_agent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_product_media", sa.Column("source_image_url", sa.String(1000), nullable=True))
    op.add_column("ai_product_media", sa.Column("request_json", sa.Text(), nullable=True))
    op.add_column("ai_product_media", sa.Column("plan_json", sa.Text(), nullable=True))
    op.add_column("ai_product_media", sa.Column("parent_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    for name in ("parent_id", "plan_json", "request_json", "source_image_url"):
        op.drop_column("ai_product_media", name)
