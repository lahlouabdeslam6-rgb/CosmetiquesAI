"""Pages éditoriales administrables, sans données initiales."""
import sqlalchemy as sa
from alembic import op
revision = "0012_site_pages"
down_revision = "0011_marketing_pack_cover"
branch_labels = None
depends_on = None
def upgrade():
    if "site_pages" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table("site_pages", sa.Column("slug",sa.String(80),primary_key=True),sa.Column("title",sa.String(180),nullable=False),sa.Column("body",sa.Text(),nullable=False))
def downgrade():
    op.drop_table("site_pages")
