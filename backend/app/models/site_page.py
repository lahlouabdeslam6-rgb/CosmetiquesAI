from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.sqlite import Base

class SitePage(Base):
    __tablename__ = "site_pages"
    slug: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(String(180))
    body: Mapped[str] = mapped_column(Text, default="")
