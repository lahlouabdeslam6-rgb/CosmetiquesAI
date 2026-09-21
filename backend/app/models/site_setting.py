from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.sqlite import Base

class SiteSetting(Base):
    __tablename__ = "site_settings"
    key: Mapped[str] = mapped_column(String(80),primary_key=True)
    value: Mapped[dict] = mapped_column(JSON,nullable=False)
