import os
import pytest
from typing import Generator, Dict
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import app
from app.api import deps
from app.core.config import settings

# Use SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database on each test case.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    Create a new FastAPI TestClient that uses the `db` fixture to override
    the `get_db` dependency that is injected into routes.
    """
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[deps.get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user() -> Dict[str, str]:
    """
    Return test user data.
    """
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }

@pytest.fixture
def test_superuser() -> Dict[str, str]:
    """
    Return test superuser data.
    """
    return {
        "email": "admin@example.com",
        "username": "admin",
        "password": "adminpassword123"
    }

@pytest.fixture
def test_auth_headers(client: TestClient, test_user: Dict[str, str]) -> Dict[str, str]:
    """
    Return authorization headers for a test user.
    """
    # Create user
    response = client.post("/api/v1/users/", json=test_user)
    assert response.status_code == 200
    
    # Login
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"],
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}
