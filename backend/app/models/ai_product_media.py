import json
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.sqlite import Base


class AIProductMedia(Base):
    __tablename__ = "ai_product_media"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    campaign_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    platform: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    placement: Mapped[str | None] = mapped_column(String(40), nullable=True)
    product_name: Mapped[str] = mapped_column(String(240))
    language: Mapped[str] = mapped_column(String(10), default="fr")
    visual_style: Mapped[str] = mapped_column(String(120), default="premium")
    requested_media_json: Mapped[str] = mapped_column(Text, default='["image"]')
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    request_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="provider_required", index=True
    )
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    @property
    def render_plan(self) -> dict | None:
        return json.loads(self.plan_json) if self.plan_json else None

    @property
    def request_spec(self) -> dict | None:
        return json.loads(self.request_json) if self.request_json else None

    @property
    def requested_media(self) -> list[str]:
        try:
            values = json.loads(self.requested_media_json)
            return [str(value) for value in values] if isinstance(values, list) else []
        except json.JSONDecodeError:
            return []
