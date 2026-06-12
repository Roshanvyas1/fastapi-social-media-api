import pytest


# Testing create post.
async def test_unauthorized_user_create_post_return_401(client):
    response = await client.post(
        "/posts/",
        json={"title": "Dummy Title", "content": "Dummy Content", "published": False},
    )
    assert response.status_code == 401


async def test_create_post_return_201(authorized_client, test_user):
    response = await authorized_client.post(
        "/posts/",
        json={"title": "Dummy Title", "content": "Dummy Content", "published": False},
    )
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Dummy Title"
    assert data["content"] == "Dummy Content"
    assert not data["published"]
    assert data["owner_id"] == test_user["id"]
    assert data["owner"]["email"] == test_user["email"]


@pytest.mark.parametrize(
    "title, content, published, status_code",
    [("", "dummy content", True, 422), ("dummy title", "", False, 422)],
)
async def test_create_post_title_or_content_cannot_be_empty_return_422(
    authorized_client, title, content, published, status_code
):
    response = await authorized_client.post(
        "/posts/", json={"title": title, "content": content, "published": published}
    )
    assert response.status_code == status_code


async def test_create_post_title_length_cannot_be_more_than_120_words_return_422(
    authorized_client,
):
    response = await authorized_client.post(
        "/posts/",
        json={"title": "a" * 121, "content": "dummy content", "published": False},
    )
    assert response.status_code == 422


# Testing get post.
async def test_unauthorized_user_get_posts_return_401(client):
    response = await client.get("/posts/")
    assert response.status_code == 401


async def test_get_posts_return_200(authorized_client, test_post):
    response = await authorized_client.get("/posts/")
    assert response.status_code == 200

    data = response.json()
    assert data[0]["Post"]["id"] == test_post.id
    assert data[0]["Post"]["title"] == test_post.title
    assert data[0]["Post"]["owner_id"] == test_post.owner_id
    assert data[0]["Post"]["owner"]["email"] == test_post.owner.email


# Testing get post using post_id.
async def test_unauthorized_user_get_post_using_post_id_return_401(client, test_post):
    id = test_post.id
    response = await client.get(f"/posts/{id}")
    assert response.status_code == 401


async def test_get_post_using_post_id_return_200(authorized_client, test_post):
    id = test_post.id
    response = await authorized_client.get(f"/posts/{id}")
    assert response.status_code == 200

    data = response.json()
    assert data["Post"]["id"] == test_post.id
    assert data["Post"]["title"] == test_post.title
    assert data["Post"]["content"] == test_post.content
    assert data["Post"]["owner_id"] == test_post.owner_id
    assert data["Post"]["owner"]["email"] == test_post.owner.email


async def test_get_post_using_post_id_does_not_exist_return_404(authorized_client):
    id = 99999
    response = await authorized_client.get(f"/posts/{id}")
    assert response.status_code == 404


async def test_get_post_using_post_id_wrong_type_return_422(authorized_client):
    id = "abc"
    response = await authorized_client.get(f"/posts/{id}")
    assert response.status_code == 422


# Testing delete post.
async def test_unauthorized_user_delete_post_using_post_id_return_401(
    client, test_post
):
    id = test_post.id
    response = await client.delete(f"/posts/{id}")
    assert response.status_code == 401


async def test_delete_post_using_post_id_belongs_to_another_user_return_403(
    authorized_client, test_post2
):
    id = test_post2.id
    response = await authorized_client.delete(f"/posts/{id}")
    assert response.status_code == 403


async def test_delete_post_using_post_id_belongs_to_owner_return_204(
    authorized_client, test_post
):
    id = test_post.id
    response = await authorized_client.delete(f"/posts/{id}")
    assert response.status_code == 204


async def test_delete_post_using_post_id_that_do_not_exist_return_404(
    authorized_client,
):
    id = 99999
    response = await authorized_client.delete(f"/posts/{id}")
    assert response.status_code == 404


async def test_delete_post_using_post_id_wrong_type_return_404(authorized_client):
    id = "abc"
    response = await authorized_client.delete(f"/posts/{id}")
    assert response.status_code == 422


# Testing update post.
async def test_unathorized_user_update_post_using_post_id_return_401(client, test_post):
    id = test_post.id
    response = await client.patch(
        f"/posts/{id}", json={"title": "Update Dummy Title", "published": False}
    )
    assert response.status_code == 401


async def test_update_post_using_post_id_belongs_another_user_return_403(
    authorized_client, test_post2
):
    id = test_post2.id
    response = await authorized_client.patch(
        f"/posts/{id}", json={"title": "Update Dummy Title", "published": False}
    )
    assert response.status_code == 403


async def test_update_post_using_post_id_return_200(authorized_client, test_post):
    id = test_post.id
    response = await authorized_client.patch(
        f"/posts/{id}", json={"title": "Update Dummy Title", "published": False}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Update Dummy Title"
    assert data["content"] == test_post.content
    assert not data["published"]
    assert data["owner_id"] == test_post.owner_id


async def test_update_post_using_post_id_does_not_exist_return_404(authorized_client):
    id = 99999
    response = await authorized_client.patch(
        f"/posts/{id}", json={"title": "Update Dummy Title", "published": False}
    )
    assert response.status_code == 404


async def test_update_post_using_post_id_wrong_type_return_422(authorized_client):
    id = "abc"
    response = await authorized_client.patch(
        f"/posts/{id}", json={"title": "Update Dummy Title", "published": False}
    )
    assert response.status_code == 422
