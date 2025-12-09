from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db_config import Base


class User(Base):
    """
    User accounts for authentication.

    Each user can create multiple short links.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationship
    links = relationship("Link", back_populates="owner", cascade="all, delete-orphan")


class Link(Base):
    """
    Short links - the core entity.

    Maps short_code to original_url.
    """

    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    short_code = Column(String(10), unique=True, nullable=False, index=True)
    original_url = Column(Text, nullable=False)
    custom_code = Column(Boolean, default=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    owner = relationship("User", back_populates="links")
    clicks = relationship("Click", back_populates="link", cascade="all, delete-orphan")


class Click(Base):
    """
    Click tracking for analytics.

    Records each time someone uses a short link.
    """

    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(
        Integer, ForeignKey("links.id", ondelete="CASCADE"), nullable=False
    )
    clicked_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    referrer = Column(String(255), nullable=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Relationship
    link = relationship("Link", back_populates="clicks")
