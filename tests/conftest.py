import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Mock STATIC_DIR to ensure tests run in API-only mode (returning JSON health check at /)
os.environ["STATIC_DIR"] = "/tmp/non_existent_accordant_test_dir"

# Import models to ensure they are registered with Base.metadata before create_all
from backend.database import SystemBase, TenantBase, get_system_db
from backend.main import app

# Use in-memory SQLite for testing
# We use shared cache/check_same_thread=False to allow sharing across threads if needed
SYSTEM_DB_URL = "sqlite:///:memory:"
TENANT_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def system_engine():
    """Create a single in-memory system database engine for the test session."""
    engine = create_engine(
        SYSTEM_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    # Ensure models are imported so they register with metadata

    # Debug prints removed for cleaner output
    SystemBase.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def tenant_engine():
    """
    Create a single in-memory tenant database engine for the test session.
    """
    engine = create_engine(
        TENANT_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TenantBase.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def system_db_session(system_engine):
    """
    Get a new session for the system DB.
    Rolls back transaction after each test to ensure isolation.
    """
    connection = system_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def tenant_db_session(tenant_engine):
    """
    Get a new session for the tenant DB.
    Rolls back transaction after each test.
    """
    connection = tenant_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def disable_rate_limiter(monkeypatch):
    """
    Disable rate limiting for all tests by default.
    Tests that specifically need to test rate limiting should override this.
    """
    # Import locally to avoid circular imports if any
    from backend.limiter import limiter

    # Store original state
    original_enabled = limiter.enabled

    # Disable
    limiter.enabled = False

    yield

    # Restore
    limiter.enabled = original_enabled


@pytest.fixture(autouse=True)
def mock_db_engines(monkeypatch, tenant_engine, system_engine):
    """
    Patch database engines/sessions to use in-memory fixtures.
    """

    # 1. Patch Tenant Engine (for get_tenant_session)
    def mock_get_engine(org_id):
        return tenant_engine

    monkeypatch.setattr("backend.database.get_tenant_engine", mock_get_engine)

    # 2. Patch System Session (for backend.organizations, etc.)
    # We need to construct a sessionmaker bound to our in-memory system_engine
    TestSystemSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=system_engine)

    # Patch where it is defined
    monkeypatch.setattr("backend.database.SystemSessionLocal", TestSystemSessionLocal)

    # Patch where it is imported (if already imported)
    # This is critical for modules that did 'from .database import SystemSessionLocal'
    import backend.organizations
    import backend.users

    monkeypatch.setattr(backend.organizations, "SystemSessionLocal", TestSystemSessionLocal)
    # Also patch backend.users since it uses SystemSessionLocal
    monkeypatch.setattr(backend.users, "SystemSessionLocal", TestSystemSessionLocal)


@pytest.fixture
def client(system_db_session):
    """
    TestClient with overridden system DB dependency.
    """

    def override_get_system_db():
        yield system_db_session

    app.dependency_overrides[get_system_db] = override_get_system_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clean_db(tenant_engine, system_engine):
    """
    Clean both databases after each test.
    """
    yield

    from sqlalchemy import text

    # Clean Tenant DB
    inspector = inspect(tenant_engine)
    with tenant_engine.begin() as conn:
        for table in inspector.get_table_names():
            conn.execute(text(f"DELETE FROM {table}"))

    # Clean System DB
    inspector_sys = inspect(system_engine)
    with system_engine.begin() as conn:
        for table in inspector_sys.get_table_names():
            conn.execute(text(f"DELETE FROM {table}"))


@pytest.fixture
def mock_personalities():
    """Mock active personalities."""
    return [
        {
            "id": "personality1",
            "name": "Personality 1",
            "model": "openai/gpt-4",
            "personality_prompt": "You are helpful.",
            "temperature": 0.7,
        },
        {
            "id": "personality2",
            "name": "Personality 2",
            "model": "anthropic/claude-3",
            "personality_prompt": "You are analytical.",
            "temperature": 0.8,
        },
    ]


@pytest.fixture
def mock_system_prompts():
    """Mock system prompts."""
    return {
        "base_system_prompt": "You are a helpful assistant.",
        "ranking_prompt": "Rank {responses_text} for {user_query}",
        "chairman_prompt": "Synthesize {user_query} using {stage1_text} and {voting_details_text}",
        "title_prompt": "Generate a title for {user_query}",
    }


@pytest.fixture
def mock_models_config():
    """Mock models configuration."""
    return {
        "chairman_model": "gemini/gemini-pro",
        "title_model": "gemini/gemini-pro",
    }
