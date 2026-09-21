"""Add the protected primary administrator flag."""

from alembic import op
import sqlalchemy as sa


revision = "0020_primary_admin"
down_revision = "0019_raw_material_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("users")}
    if "is_super_admin" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "is_super_admin",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
    op.execute(
        """
        UPDATE users
        SET is_super_admin = 1
        WHERE id = (
            SELECT id FROM users
            WHERE role = 'admin' AND is_deleted = 0
            ORDER BY created_at ASC, id ASC
            LIMIT 1
        )
        AND NOT EXISTS (
            SELECT 1 FROM users WHERE is_super_admin = 1 AND is_deleted = 0
        )
        """
    )


def downgrade() -> None:
    op.drop_column("users", "is_super_admin")
