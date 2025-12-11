from unittest.mock import patch

import db_models


def test_create_link(authenticated_client):
    """Test that a user can create a link"""

    response = authenticated_client.post(
        "/links",
        json={
            "original_url": "https://example.com/",
            "expires_at": "2026-12-15T00:00:00Z",
        },
    )
    assert response.status_code == 201
    response_data = response.json()
    assert "short_code" in response_data
    assert response_data["expires_at"] == "2026-12-15T00:00:00Z"
    assert "created_at" in response_data


def test_custom_link(authenticated_client):
    """Test that user can create a custom link code"""

    response = authenticated_client.post(
        "/links",
        json={
            "original_url": "https://example.com/",
            "custom_code": "test123",
            "expires_at": "2026-12-15T00:00:00Z",
        },
    )
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["custom_code"] == True


def test_collision_retry_logic(authenticated_client, db_session):

    blocker_code = "TAKEN1"
    blocker_link = db_models.Link(
        user_id=1,
        original_url="http://blocker.com",
        short_code=blocker_code,
        custom_code=False,
    )
    db_session.add(blocker_link)
    db_session.commit()

    with patch("routers.links.generate_short_code", side_effect=["TAKEN1", "WORKS2"]):
        response = authenticated_client.post(
            "/links", json={"original_url": "https://example.com/"}
        )

    assert response.status_code == 201
    data = response.json()

    assert data["short_code"] == "WORKS2"

    links = db_session.query(db_models.Link).all()
    assert len(links) == 2


def test_collision_max_retries(authenticated_client, db_session):
    """Test that we get 500 error after 3 failed collision attempts"""

    for code in ["TRY1", "TRY2", "TRY3"]:
        blocker = db_models.Link(
            user_id=1,
            short_code=code,
            original_url="http://blocker.com",
            custom_code=False,
        )
        db_session.add(blocker)
    db_session.commit()

    with patch(
        "routers.links.generate_short_code", side_effect=["TRY1", "TRY2", "TRY3"]
    ):
        response = authenticated_client.post(
            "/links", json={"original_url": "https://example.com/"}
        )

    assert response.status_code == 500
    assert "Could not generate unique short code" in response.json()["detail"]
