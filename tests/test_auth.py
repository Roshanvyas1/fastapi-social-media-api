import jwt
import pytest
from app.config import settings


# Testing login credentials.
async def test_login_user_credentials_does_not_exist_return_403(client):
    response = await client.post(
        "/login", data={"username": "unknown@gmail.com", "password": "unknown123"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid email or password!"


async def test_login_invalid_user_password_return_403(client, test_user):
    response = await client.post(
        "/login", data={"username": test_user["email"], "password": "wrongpassword"}
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
        "/login", data={"username": username, "password": password}
    )
    assert response.status_code == status_code


async def test_login_user_credentials_return_200(client, test_user):
    response = await client.post(
        "/login", data={"username": test_user["email"], "password": "dummy123"}
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
