import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app.core.database import Base, get_db
from src.app.main import app
from src.app.routers.auth import LOGIN_ATTEMPTS

# In-memory test database shared across threads
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    LOGIN_ATTEMPTS.clear()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    LOGIN_ATTEMPTS.clear()


@pytest.fixture
def db_session():
    """Provides a fresh transactional database session for unit tests."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client():
    """TestClient that overrides get_db dependency with test database."""

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers_user_a(client: TestClient):
    """Registers and authenticates User A, returning auth headers."""
    reg_payload = {
        "email": "user_a@spema.internal",
        "username": "user_a",
        "password": "SecurePassword123!",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {"email_or_username": "user_a", "password": "SecurePassword123!"}
    resp = client.post("/api/v1/auth/login", json=login_payload)
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user_b(client: TestClient):
    """Registers and authenticates User B, returning auth headers."""
    reg_payload = {
        "email": "user_b@spema.internal",
        "username": "user_b",
        "password": "SecurePassword123!",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {"email_or_username": "user_b", "password": "SecurePassword123!"}
    resp = client.post("/api/v1/auth/login", json=login_payload)
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
