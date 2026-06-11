# Testing user voting post.
async def test_unauthorized_vote_or_unvote_post_id_return_401(client, test_post):
    response = await client.post("/votes/", json={
        "post_id": test_post.id,
        "dir": 1    # or 0
    })
    assert response.status_code == 401

async def test_vote_or_unvote_post_id_does_not_exist_return_404(authorized_client):
    response = await authorized_client.post("/votes/", json={
        "post_id": 99999,
        "dir": 1    # or 0
    })
    assert response.status_code == 404

async def test_vote_or_unvote_post_id_wrong_type_return_422(authorized_client):
    response = await authorized_client.post("/votes/", json={
        "post_id": "abc",
        "dir": 1     # or 0
    })
    assert response.status_code == 422

async def test_vote_post_id_return_200(authorized_client, test_post):
    response = await authorized_client.post("/votes/", json={
        "post_id": test_post.id,
        "dir": 1
    })
    assert response.status_code == 200
    assert response.json()['message'] == "Successfully voted!"

async def test_vote_post_id_already_exist_return_409(authorized_client, test_vote):
    response = await authorized_client.post("/votes/", json={
        "post_id": test_vote.post_id,
        "dir": 1
    })
    assert response.status_code == 409
    assert response.json()['detail'] == 'Your vote had already registered!'

async def test_unvote_post_id_return_200(authorized_client, test_vote):
    response = await authorized_client.post("/votes/", json={
        "post_id": test_vote.post_id,
        "dir": 0
    })
    assert response.status_code == 200
    assert response.json()['message'] == "Successfully unvoted!"

async def test_unvote_post_id_in_which_vote_does_not_exist_return_404(authorized_client, test_post):
    response = await authorized_client.post("/votes/", json={
        "post_id": test_post.id,
        "dir": 0
    })
    assert response.status_code == 404
    assert response.json()['detail'] == "Your vote doesn't exist!"

async def test_multiple_unvote_post_id_return_404(authorized_client, test_vote):
    response = await authorized_client.post("/votes/", json={
        "post_id": test_vote.post_id,
        "dir": 0
    })
    assert response.status_code == 200
    assert response.json()['message'] == "Successfully unvoted!"

    response = await authorized_client.post("/votes/", json={
        "post_id": test_vote.post_id,
        "dir": 0
    })
    assert response.status_code == 404
    assert response.json()['detail'] == "Your vote doesn't exist!"