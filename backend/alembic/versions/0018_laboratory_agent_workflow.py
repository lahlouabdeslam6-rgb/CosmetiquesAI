"""Authenticated custom cosmetic workflow and laboratory report.

Revision ID: 0018_laboratory_agent_workflow
Revises: 0017_media_description_plans
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_laboratory_agent_workflow"
down_revision = "0017_media_description_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("cosmetic_requests")}
    additions = {
        # SQLite cannot add FK constraints to an existing table without rebuilding it.
        # The ORM still declares the relation; the migration adds compatible ID columns.
        "user_id": sa.Column("user_id", sa.Integer(), nullable=True),
        "project_name": sa.Column("project_name", sa.String(180), nullable=True),
        "client_snapshot_json": sa.Column("client_snapshot_json", sa.Text(), nullable=False, server_default="{}"),
        "lab_report_json": sa.Column("lab_report_json", sa.Text(), nullable=True),
        "material_decision_json": sa.Column("material_decision_json", sa.Text(), nullable=False, server_default="{}"),
        "admin_feedback": sa.Column("admin_feedback", sa.Text(), nullable=True),
        "revision": sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        "product_id": sa.Column("product_id", sa.Integer(), nullable=True),
        "approved_by": sa.Column("approved_by", sa.Integer(), nullable=True),
        "approved_at": sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    }
    for name, column in additions.items():
        if name not in columns:
            op.add_column("cosmetic_requests", column)
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("cosmetic_requests")}
    if "ix_cosmetic_requests_user_id" not in indexes:
        op.create_index("ix_cosmetic_requests_user_id", "cosmetic_requests", ["user_id"])


def downgrade() -> None:
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("cosmetic_requests")}
    if "ix_cosmetic_requests_user_id" in indexes:
        op.drop_index("ix_cosmetic_requests_user_id", table_name="cosmetic_requests")
    for name in (
        "approved_at", "approved_by", "product_id", "revision", "admin_feedback",
        "material_decision_json", "lab_report_json", "client_snapshot_json",
        "project_name", "user_id",
    ):
        op.drop_column("cosmetic_requests", name)
