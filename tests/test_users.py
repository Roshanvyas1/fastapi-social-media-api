import pytest


# Testing /api/v1/users/ endpoints.
async def test_unauthorized_get_users_return_401(client):
    response = await client.get("/api/v1/users/")
    assert response.status_code == 401


async def test_get_users_return_200(authorized_client, test_user, test_user2):
    response = await authorized_client.get("/api/v1/users/")
    assert response.status_code == 200

    data = response.json()
    assert data[0]["id"] == test_user["id"]
    assert data[0]["email"] == test_user["email"]
    assert data[1]["id"] == test_user2["id"]
    assert data[1]["email"] == test_user2["email"]
    assert "password" not in data[0]
    assert "password" not in data[1]


@pytest.mark.parametrize(
    "limit, skip, search, status_code",
    [
        (-1, 0, "", 422),
        (1000, 0, "", 422),
        ("abc", 0, "", 422),
        (10, -1, "", 422),
        ("10", "abc", "", 422),
    ],
)
async def test_get_users_wrong_type_or_limit_return_422(
    authorized_client, limit, skip, search, status_code
):
    response = await authorized_client.get(
        f"/api/v1/users/?limit={limit}&skip={skip}&search={search}"
    )
    assert response.status_code == status_code


# Testing /api/v1/users/me endpoint.
async def test_unauthorized_get_users_me_return_401(client):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


async def test_get_users_me_return_200(
    authorized_client, test_user, test_post, test_post2
):
    response = await authorized_client.get("/api/v1/users/me")
    assert response.status_code == 200

    data = response.json()
    assert data["user"]["id"] == test_user["id"]
    assert data["user"]["email"] == test_user["email"]
    assert data["posts"][0]["id"] == test_post.id
    assert data["posts"][0]["title"] == test_post.title
    assert data["posts"][0]["content"] == test_post.content
    assert data["posts"][0]["published"] == test_post.published
    assert data["posts"][0]["votes"] == 0
    assert not data["posts"][0]["voted"]


# Testing /api/v1/users/{id} endpoint.
async def test_unauthorized_get_user_using_id_return_401(client, test_user2):
    response = await client.get(f"/api/v1/users/{test_user2['id']}")
    assert response.status_code == 401


async def test_get_user_using_id_return_200(authorized_client, test_user2, test_post2):
    response = await authorized_client.get(f"/api/v1/users/{test_user2['id']}")
    assert response.status_code == 200

    data = response.json()
    assert data["user"]["id"] == test_user2["id"]
    assert data["user"]["email"] == test_user2["email"]
    assert data["posts"][0]["id"] == test_post2.id
    assert data["posts"][0]["title"] == test_post2.title
    assert data["posts"][0]["content"] == test_post2.content
    assert data["posts"][0]["published"] == test_post2.published
    assert data["posts"][0]["votes"] == 0
    assert not data["posts"][0]["voted"]
