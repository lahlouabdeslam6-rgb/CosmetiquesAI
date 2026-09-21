"""Configuration des rubriques sans données métier initiales."""
import sqlalchemy as sa
from alembic import op
revision="0013_site_settings"
down_revision="0012_site_pages"
branch_labels=None
depends_on=None
def upgrade():
    if "site_settings" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table("site_settings",sa.Column("key",sa.String(80),primary_key=True),sa.Column("value",sa.JSON(),nullable=False))
def downgrade():
    op.drop_table("site_settings")
