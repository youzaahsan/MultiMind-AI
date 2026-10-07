import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.database.models import User
from app.database.repositories import UserRepository

client = TestClient(app)


def test_fresh_user_default_name():
    """Verify fresh user without explicit name defaults to 'User' or normalized email name."""
    db = SessionLocal()
    try:
        rand_id = uuid.uuid4().hex[:8]
        email = f"fresh_{rand_id}@multimind.ai"
        user = UserRepository.create(db, email, "Password123!", full_name=None)
        assert user.full_name is not None
        assert len(user.full_name) > 0

        email2 = f"default_{rand_id}@multimind.ai"
        user2 = UserRepository.create(db, email2, "Password123!", full_name="User")
        assert user2.full_name == "User"
    finally:
        db.close()


def test_profile_api_get_and_update():
    """Verify authenticated GET and PUT /api/user/profile endpoints."""
    rand_id = uuid.uuid4().hex[:8]
    test_email = f"ahmed_khan_{rand_id}@multimind.ai"
    reg_res = client.post(
        "/auth/register",
        json={"email": test_email, "password": "Password123!", "full_name": "User"},
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get initial profile
    get_res = client.get("/api/user/profile", headers=headers)
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["email"] == test_email

    # 2. Update profile to "Ahmed Khan"
    put_res = client.put(
        "/api/user/profile",
        headers=headers,
        json={"full_name": "Ahmed Khan"},
    )
    assert put_res.status_code == 200
    updated_data = put_res.json()
    assert updated_data["full_name"] == "Ahmed Khan"

    # 3. Verify persistence with a fresh GET
    verify_res = client.get("/api/user/profile", headers=headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["full_name"] == "Ahmed Khan"


def test_profile_update_validation():
    """Verify empty name rejection on profile update."""
    rand_id = uuid.uuid4().hex[:8]
    test_email = f"val_{rand_id}@multimind.ai"
    reg_res = client.post(
        "/auth/register",
        json={"email": test_email, "password": "Password123!", "full_name": "Tester"},
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Whitespace only should fail
    bad_res = client.put(
        "/api/user/profile",
        headers=headers,
        json={"full_name": "   "},
    )
    assert bad_res.status_code in (400, 422)
