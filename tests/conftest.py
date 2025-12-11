import os

# Set testing flag (in case you add rate limiting later)
os.environ["TESTING"] = "true"

from unittest.mock import patch

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import db_models
from db_config import Base, get_db
from main import app
from redis_config import get_redis

# TEST DATABASE CONFIGURATION
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://urlshort_user:odysbase@localhost:5432/urlshortener_test",
)

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Redis client for clearing cache
test_redis_client = redis.Redis(
    host="localhost", port=6379, db=1, decode_responses=True
)


# DATABASE FIXTURES
@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.
    Creates all tables before test, drops them after test.
    """
    # Create all tables in the test database
    Base.metadata.create_all(bind=test_engine)

    # Create a new session for the test
    session = TestSessionLocal()

    # Clear Redis cache before each test
    test_redis_client.flushdb()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test (clean slate for next test)
        Base.metadata.drop_all(bind=test_engine)


# CLIENT FIXTURE
@pytest.fixture(scope="function")
def client(db_session, override_redis):
    """
    Creates a test client with overridden database dependency.
    """

    # Override the get_db dependency to use our test database
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(app) as test_client:
        yield test_client

    # Clean up: remove the override
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def override_redis():
    """Override Redis to use test database"""

    def get_test_redis():
        return test_redis_client

    app.dependency_overrides[get_redis] = get_test_redis
    yield


@pytest.fixture(scope="function")
def test_redis():
    """Provides the test Redis client to tests that need direct Redis access"""
    return test_redis_client


# AUTHENTICATION FIXTURES
@pytest.fixture(scope="function")
def test_user(client):
    """
    Creates a test user and returns their credentials
    """
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    }

    # Register the user
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    # Return the credentials (including password for login)
    return user_data


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    """
    Creates a user and returns their authentication token.
    """
    # Login with the test user
    login_response = client.post(
        "/auth/login",
        json={"username": test_user["username"], "password": test_user["password"]},
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    return token


@pytest.fixture(scope="function")
def authenticated_client(client, auth_token):
    """
    Returns a client with authentication headers already set.
    """
    # Add the Authorization header to the client
    client.headers = {**client.headers, "Authorization": f"Bearer {auth_token}"}

    return client


@pytest.fixture(scope="function")
def create_user_and_token(client):
    """
    Factory fixture that creates a user and returns their token.
    Can be called multiple times to create multiple users.
    """

    def _create_user(username: str, email: str, password: str):
        # Register user
        client.post(
            "/auth/register",
            json={"username": username, "email": email, "password": password},
        )

        # Login and get token
        login_response = client.post(
            "/auth/login", json={"username": username, "password": password}
        )

        return login_response.json()["access_token"]

    return _create_user


@pytest.fixture(scope="function", autouse=True)
def patch_background_tasks_db(db_session):
    """
    Forces background tasks to use the same Test Database as the rest of the test.
    Patches SessionLocal imported in routers/redirect.py
    """

    def test_session_factory():
        return TestSessionLocal()

    # IMPORTANT: Patch the location where SessionLocal is imported
    with patch("routers.redirect.SessionLocal", side_effect=test_session_factory):
        yield
