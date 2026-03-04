"""
SQLAlchemy ORM models for the items and categories tables.
Mirrors the schema defined in schema.sql exactly.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, ARRAY, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, unique=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False, unique=True)
    title = Column(Text, nullable=False)
    content = Column(Text)              # full extracted text (may be long)
    summary = Column(Text)              # 2-3 sentence AI-generated summary
    tags = Column(ARRAY(String))        # 3-5 AI tags from Gemini
    manual_tags = Column(ARRAY(String), default=list)  # user-added tags
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"))
    favicon_url = Column(Text)
    embedding = Column(Vector(768))     # text-embedding-004 produces 768-dim vectors
    status = Column(String, default="pending")  # 'pending' | 'processed' | 'failed'
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        """Serialize to a JSON-safe dict (excludes the raw embedding vector)."""
        return {
            "id": str(self.id),
            "url": self.url,
            "title": self.title,
            "summary": self.summary,
            "tags": self.tags or [],
            "manual_tags": self.manual_tags or [],
            "category_id": str(self.category_id) if self.category_id else None,
            "favicon_url": self.favicon_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DemoItem(Base):
    """
    Read-only pre-seeded demo items — completely isolated from real user data.
    No auth required to read these. No Gemini calls at runtime — data is pre-written.
    """
    __tablename__ = "demo_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False, unique=True)
    title = Column(Text, nullable=False)
    summary = Column(Text)
    tags = Column(ARRAY(String))
    category = Column(Text)        # category name stored as text (no FK — demo is standalone)
    source = Column(Text)          # e.g. "openai.com", "youtube.com"
    favicon_url = Column(Text)
    saved_date = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "url": self.url,
            "title": self.title,
            "summary": self.summary,
            "tags": self.tags or [],
            "category": self.category,
            "source": self.source,
            "favicon_url": self.favicon_url,
            "saved_date": self.saved_date.isoformat() if self.saved_date else None,
        }
