"""Raw-material stock and cosmetic formulation requests."""
import sqlalchemy as sa
from alembic import op

revision = "0014_cosmetic_formulation"
down_revision = "0013_site_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "raw_materials" not in tables:
        op.create_table(
            "raw_materials",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(180), nullable=False, unique=True),
            sa.Column("reference", sa.String(80), nullable=True),
            sa.Column("unit", sa.String(20), nullable=False, server_default="g"),
            sa.Column("quantity", sa.Float(), nullable=False, server_default="0"),
            sa.Column("reserved_quantity", sa.Float(), nullable=False, server_default="0"),
            sa.Column("minimum_quantity", sa.Float(), nullable=False, server_default="0"),
            sa.Column("cost_per_unit", sa.Float(), nullable=True),
            sa.Column("supplier", sa.String(180), nullable=True),
            sa.Column("expires_on", sa.Date(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_raw_materials_reference", "raw_materials", ["reference"])
        op.create_index("ix_raw_materials_is_active", "raw_materials", ["is_active"])
    if "cosmetic_requests" not in tables:
        op.create_table(
            "cosmetic_requests",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("reference", sa.String(24), nullable=False, unique=True),
            sa.Column("client_name", sa.String(180), nullable=False),
            sa.Column("email", sa.String(240), nullable=False),
            sa.Column("phone", sa.String(40), nullable=False),
            sa.Column("product_type", sa.String(120), nullable=False),
            sa.Column("needs", sa.Text(), nullable=False, server_default=""),
            sa.Column("answers_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("status", sa.String(40), nullable=False, server_default="received"),
            sa.Column("formula_json", sa.Text(), nullable=True),
            sa.Column("missing_materials_json", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("ai_note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_cosmetic_requests_reference", "cosmetic_requests", ["reference"])
        op.create_index("ix_cosmetic_requests_email", "cosmetic_requests", ["email"])
        op.create_index("ix_cosmetic_requests_product_type", "cosmetic_requests", ["product_type"])
        op.create_index("ix_cosmetic_requests_status", "cosmetic_requests", ["status"])
        op.create_index("ix_cosmetic_requests_created_at", "cosmetic_requests", ["created_at"])


def downgrade() -> None:
    op.drop_table("cosmetic_requests")
    op.drop_table("raw_materials")
