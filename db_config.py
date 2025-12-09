"""
Database configuration and session management.

This module handles:
1. Reading DATABASE_URL from environment
2. Creating SQLAlchemy engine
3. Providing database sessions
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Pydantic validates types and provides defaults.
    Reads from .env file automatically.
    """

    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env")


# Singleton instance - created once, imported everywhere
settings = Settings()  # type: ignore


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Test connections before using them
    echo=False,  # Set to True to see SQL queries (debug)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI

    Provides a database session to route handlers.
    Automatically closes session when request completes.

    Usage in routes:
        def my_route(db: Session = Depends(get_db))
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
