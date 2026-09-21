from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


MediaKind = Literal["image", "video"]


class ProductMediaPrepareRequest(BaseModel):
    product_id: int = Field(ge=1)
    campaign_id: int | None = Field(default=None, ge=1)
    platform: Literal["instagram", "facebook", "tiktok"] | None = None
    placement: Literal["feed", "story", "reel", "video"] | None = None
    source_mode: Literal["upload", "agent"] = "upload"
    language: Literal["fr", "ar", "darija"] = "fr"
    visual_style: str = Field(default="premium naturel", min_length=3, max_length=120)
    requested_media: list[MediaKind] = Field(
        default_factory=lambda: ["image", "video"], min_length=1, max_length=2
    )
    instructions: str | None = Field(default=None, max_length=1500)
    image_description: str | None = Field(default=None, max_length=1500)
    video_description: str | None = Field(default=None, max_length=1500)
    parent_id: int | None = Field(default=None, ge=1)
    feedback: str | None = Field(default=None, max_length=1500)


class ProductMediaDraftUpdate(BaseModel):
    image_prompt: str | None = Field(default=None, min_length=20, max_length=5000)
    video_prompt: str | None = Field(default=None, min_length=20, max_length=5000)


class ProductMediaResultRequest(BaseModel):
    provider: str = Field(min_length=2, max_length=80)
    image_url: str | None = Field(default=None, max_length=1000)
    video_url: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def require_result(self) -> "ProductMediaResultRequest":
        if not self.image_url and not self.video_url:
            raise ValueError("Une image ou une vidéo générée est requise")
        return self


class ProductMediaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    campaign_id: int | None = None
    platform: str | None = None
    placement: str | None = None
    product_name: str
    language: str
    visual_style: str
    requested_media: list[str]
    instructions: str | None
    image_prompt: str | None
    video_prompt: str | None
    status: str
    provider: str | None
    image_url: str | None
    video_url: str | None
    error_message: str | None
    created_by: int
    approved_by: int | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    source_image_url: str | None = None
    source_mode: str = "upload"
    request_spec: dict | None = None
    render_plan: dict | None = None
    parent_id: int | None = None


class ProductMediaListResponse(BaseModel):
    items: list[ProductMediaResponse]
    total: int
