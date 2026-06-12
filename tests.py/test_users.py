import pytest


# Testing user create.
async def test_user_email_return_201(test_user):
    assert test_user["email"] == "dummy@gmail.com"


async def test_user_password_should_not_return_in_response(test_user):
    assert "password" not in test_user


async def test_duplicate_user_return_409(test_user, client):
    assert test_user["email"] == "dummy@gmail.com"
    assert "password" not in test_user

    response = await client.post(
        "/users/", json={"email": "dummy@gmail.com", "password": "dummy123"}
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
    response = await client.post("/users/", json={"email": email, "password": password})
    assert response.status_code == status_code


async def test_user_insufficient_password_length_less_than_8_charactor_return_422(
    client,
):
    response = await client.post(
        "/users/", json={"email": "dummy@gmail.com", "password": "dummy"}
    )
    assert response.status_code == 422
