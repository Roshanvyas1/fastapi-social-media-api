import jwt
import pytest
from app.config import settings


# Testing /api/v1/auth/register endpoint.
async def test_user_email_return_201(test_user):
    assert test_user["email"] == "dummy@gmail.com"


async def test_user_password_should_not_return_in_response(test_user):
    assert "password" not in test_user


async def test_duplicate_user_return_409(test_user, client):
    assert test_user["email"] == "dummy@gmail.com"
    assert "password" not in test_user

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dummy@gmail.com", "password": "dummy123"},
    )
    assert response.status_code == 409


@pytest.mark.parametrize(
    "email, password, status_code",
    [
        ("dummygmail.com", "dummy123", 422),
        (None, "dummy123", 422),
        ("dummy@gmail.com", "dummy", 422),
        ("dummy@gmail.com", None, 422),
    ],
)
async def test_user_wrong_email_or_password_format_return_422(
    client, email, password, status_code
):
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert response.status_code == status_code


async def test_user_insufficient_password_length_less_than_8_charactor_return_422(
    client,
):
    response = await client.post(
        "/api/v1/auth/register", json={"email": "dummy@gmail.com", "password": "dummy"}
    )
    assert response.status_code == 422


# Testing /api/v1/auth/login.
async def test_login_user_credentials_does_not_exist_return_403(client):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "unknown@gmail.com", "password": "unknown123"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid email or password!"


async def test_login_invalid_user_password_return_403(client, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid email or password!"


@pytest.mark.parametrize(
    "username, password, status_code",
    [("", "unknown123", 422), ("dummy@gmail.com", "", 422)],
)
async def test_login_user_credentials_cannot_be_empty_return_422(
    client, username, password, status_code
):
    response = await client.post(
        "/api/v1/auth/login", data={"username": username, "password": password}
    )
    assert response.status_code == status_code


async def test_login_user_credentials_return_200(client, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": "dummy123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "Bearer"

    token = response.json()["access_token"]
    data = jwt.decode(
        jwt=token, key=settings.secret_key, algorithms=[settings.algorithm]
    )
    user_id = data["user_id"]
    assert test_user["id"] == user_id


# Testing /api/v1/auth/change-password endpoint.
async def test_unauthorized_user_password_change_return_401(client):
    response = await client.patch("/api/v1/auth/change-password")
    assert response.status_code == 401


@pytest.mark.parametrize(
    "curr_password, new_password, confirm_password, status_code",
    [
        ("abc", "dummy123", "dummy123", 422),
        ("dummy123", "abc", "dummy123", 422),
        ("dummy123", "dummy123", "abc", 422),
    ],
)
async def test_user_password_change_contain_less_than_8_charactor_return_422(
    authorized_client, curr_password, new_password, confirm_password, status_code
):
    response = await authorized_client.patch(
        "/api/v1/auth/change-password",
        json={
            "current_password": curr_password,
            "new_password": new_password,
            "confirm_password": confirm_password,
        },
    )
    assert response.status_code == status_code


async def test_user_new_password_must_be_different_return_400(authorized_client):
    response = await authorized_client.patch(
        "/api/v1/auth/change-password",
        json={
            "current_password": "dummy123",
            "new_password": "dummy123",
            "confirm_password": "dummy123",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "New and Current password must be different."


async def test_user_confirm_password_must_be_same_return_400(authorized_client):
    response = await authorized_client.patch(
        "/api/v1/auth/change-password",
        json={
            "current_password": "dummy123",
            "new_password": "dummy123",
            "confirm_password": "unknown123",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "New and Confirm password must Match."


async def test_user_change_wrong_password_return_403(authorized_client):
    response = await authorized_client.patch(
        "/api/v1/auth/change-password",
        json={
            "current_password": "unknown123",
            "new_password": "dummy123",
            "confirm_password": "dummy123",
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid Credential."


async def test_user_password_change_return_200(authorized_client):
    response = await authorized_client.patch(
        "/api/v1/auth/change-password",
        json={
            "current_password": "dummy123",
            "new_password": "dummy12345",
            "confirm_password": "dummy12345",
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password has been changed successfully."
