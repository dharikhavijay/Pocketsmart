import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.auth_service import AuthService
from app.database import Base, engine, SessionLocal
from app.models.user import User

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup


def test_password_hashing():
    raw_pwd = "SecurePassword123"
    hashed = AuthService.hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert AuthService.verify_password(raw_pwd, hashed) is True
    assert AuthService.verify_password("WrongPassword", hashed) is False


def test_jwt_token_flow():
    token = AuthService.create_access_token(data={"sub": "testuser"})
    payload = AuthService.decode_token(token)
    assert payload is not None
    assert payload.get("sub") == "testuser"


def test_register_and_login():
    unique_user = "tester_auth_1"
    unique_email = "tester_auth_1@example.com"

    # Clean existing user if any
    db = SessionLocal()
    existing = db.query(User).filter(User.username == unique_user).first()
    if existing:
        db.delete(existing)
        db.commit()
    db.close()

    # Register via JSON
    reg_response = client.post(
        "/register",
        json={
            "username": unique_user,
            "email": unique_email,
            "full_name": "Test User",
            "password": "mypassword123"
        }
    )
    assert reg_response.status_code == 200
    assert "access_token" in reg_response.json()

    # Login via JSON
    login_response = client.post(
        "/login",
        json={
            "username_or_email": unique_user,
            "password": "mypassword123"
        }
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    # Invalid login
    bad_login = client.post(
        "/login",
        json={
            "username_or_email": unique_user,
            "password": "wrongpassword"
        }
    )
    assert bad_login.status_code == 401
