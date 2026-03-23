def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_user(client):
    response = client.post("/users/", json={
        "email": "pranav@example.com",
        "name": "Pranav"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "pranav@example.com"
    assert data["name"] == "Pranav"
    assert data["id"] == 1
    assert data["is_active"] == True
    assert data["is_profile_complete"] == False


def test_create_user_duplicate_email(client):
    # Create first user
    client.post("/users/", json={
        "email": "pranav@example.com",
        "name": "Pranav"
    })
    # Try creating second user with same email
    response = client.post("/users/", json={
        "email": "pranav@example.com",
        "name": "Someone Else"
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_get_user(client):
    # First create a user
    client.post("/users/", json={
        "email": "pranav@example.com",
        "name": "Pranav"
    })
    # Then fetch them
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["email"] == "pranav@example.com"


def test_get_user_not_found(client):
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_user(client):
    # Create user first
    client.post("/users/", json={
        "email": "pranav@example.com",
        "name": "Pranav"
    })
    # Update only bio
    response = client.patch("/users/1", json={
        "bio": "Learning FastAPI"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["bio"] == "Learning FastAPI"
    assert data["name"] == "Pranav"  # name unchanged


def test_update_user_name_only(client):
    client.post("/users/", json={
        "email": "pranav@example.com",
        "name": "Pranav"
    })
    response = client.patch("/users/1", json={"name": "Pranav Rathod"})
    assert response.status_code == 200
    assert response.json()["name"] == "Pranav Rathod"


def test_delete_user(client):
    # Create user
    client.post("/users/", json={
        "email": "pranav@example.com",
        "name": "Pranav"
    })
    # Delete them
    response = client.delete("/users/1")
    assert response.status_code == 200

    # They should no longer appear in list
    list_response = client.get("/users/")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 0


def test_list_users(client):
    # Create two users
    client.post("/users/", json={"email": "user1@example.com", "name": "User One"})
    client.post("/users/", json={"email": "user2@example.com", "name": "User Two"})

    response = client.get("/users/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_users_pagination(client):
    # Create 3 users
    for i in range(3):
        client.post("/users/", json={
            "email": f"user{i}@example.com",
            "name": f"User {i}"
        })
    # Request only 2
    response = client.get("/users/?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2