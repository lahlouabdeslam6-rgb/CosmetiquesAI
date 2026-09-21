"""Attach the source catalogue to raw-material stock records."""
from alembic import op
import sqlalchemy as sa

revision = "0019_raw_material_catalog"
down_revision = "0018_laboratory_agent_workflow"
branch_labels = None
depends_on = None

def upgrade():
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("raw_materials")}
    if "catalog_json" not in columns:
        op.add_column("raw_materials", sa.Column("catalog_json", sa.Text(), nullable=False, server_default="{}"))

def downgrade():
    op.drop_column("raw_materials", "catalog_json")
