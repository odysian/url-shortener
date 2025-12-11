def test_register_user(client):
    """Test user registration"""
    response = client.post(
        "/auth/register",
        json={
            "username": "chris",
            "email": "chris@example.com",
            "password": "testpass123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "chris"
    assert data["email"] == "chris@example.com"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_username(client, test_user):
    """Test that registering with an existing username fails"""

    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "different@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 409


def test_login_success(client, test_user):
    """Test that a user can login with correct credentials"""

    response = client.post(
        "/auth/login",
        json={"username": test_user["username"], "password": test_user["password"]},
    )

    assert response.status_code == 200

    response_data = response.json()
    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"


def test_login_invalid_password(client, test_user):
    """Test that login fails with wrong password"""

    response = client.post(
        "/auth/login",
        json={"username": test_user["username"], "password": "wrong_password"},
    )
    assert response.status_code == 401
