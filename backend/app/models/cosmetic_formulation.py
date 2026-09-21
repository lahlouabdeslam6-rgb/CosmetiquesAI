from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.sqlite import Base


class RawMaterial(Base):
    __tablename__ = "raw_materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    reference: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    catalog_json: Mapped[str] = mapped_column(Text, default="{}")
    unit: Mapped[str] = mapped_column(String(20), default="g")
    quantity: Mapped[float] = mapped_column(Float, default=0)
    reserved_quantity: Mapped[float] = mapped_column(Float, default=0)
    minimum_quantity: Mapped[float] = mapped_column(Float, default=0)
    cost_per_unit: Mapped[float | None] = mapped_column(Float, nullable=True)
    supplier: Mapped[str | None] = mapped_column(String(180), nullable=True)
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class CosmeticRequest(Base):
    __tablename__ = "cosmetic_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    project_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    client_name: Mapped[str] = mapped_column(String(180))
    email: Mapped[str] = mapped_column(String(240), index=True)
    phone: Mapped[str] = mapped_column(String(40))
    product_type: Mapped[str] = mapped_column(String(120), index=True)
    needs: Mapped[str] = mapped_column(Text, default="")
    answers_json: Mapped[str] = mapped_column(Text, default="{}")
    client_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(40), default="received", index=True)
    formula_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    formulas_json: Mapped[str] = mapped_column(Text, default="[]")
    conversation_json: Mapped[str] = mapped_column(Text, default="[]")
    selected_formula_index: Mapped[int] = mapped_column(Integer, default=0)
    lab_report_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    missing_materials_json: Mapped[str] = mapped_column(Text, default="[]")
    material_decision_json: Mapped[str] = mapped_column(Text, default="{}")
    ai_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
