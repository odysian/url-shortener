from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

# User Models


class UserCreate(BaseModel):
    """Request model for user registration."""

    username: str = Field(min_length=3, max_length=50)
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=100)


class UserResponse(BaseModel):
    """Response model for user data."""

    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Request model for login."""

    username: str
    password: str


class Token(BaseModel):
    """Response model for authentication tokens."""

    access_token: str
    token_type: str


# Link Models


class LinkCreate(BaseModel):
    """
    Request model for creating a short link.

    User provides the URL to shorten.
    Optionally can specify custom short code.
    """

    original_url: HttpUrl  # Validates URL format
    custom_code: Optional[str] = Field(None, min_length=3, max_length=10)
    expires_at: Optional[datetime] = None


class LinkUpdate(BaseModel):
    """
    Request model for updating a link.

    Can change destination URL or expiration.
    Cannot change short_code (would break existing links).
    """

    original_url: Optional[HttpUrl] = None
    expires_at: Optional[datetime] = None


class LinkResponse(BaseModel):
    """
    Response model for link data.

    Returns all link info including generated short_code.
    """

    id: int
    user_id: int
    short_code: str
    original_url: str
    custom_code: bool
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LinkWithStats(BaseModel):
    """
    Extended response model that includes click statistics.

    Used for detailed link view.
    """

    id: int
    user_id: int
    short_code: str
    original_url: str
    custom_code: bool
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    total_clicks: int

    model_config = ConfigDict(from_attributes=True)


# Click Models


class ClickResponse(BaseModel):
    """Response model for individual click records."""

    id: int
    link_id: int
    clicked_at: datetime
    referrer: Optional[str]
    user_agent: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ClickStats(BaseModel):
    """
    Aggregated statistics for a link.

    Summary of click data for analytics dashboard.
    """

    total_clicks: int
    clicks_today: int
    clicks_this_week: int
    clicks_this_month: int
    top_referrers: list[dict]  # [{"referrer": "twitter.com", "count": 42}, ...]
