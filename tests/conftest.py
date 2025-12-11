import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database import SystemBase, TenantBase, get_system_db
from backend.main import app

# Use in-memory SQLite for testing
# We use shared cache/check_same_thread=False to allow sharing across threads if needed
SYSTEM_DB_URL = "sqlite:///:memory:"
TENANT_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def system_engine():
    """Create a single in-memory system database engine for the test session."""
    engine = create_engine(SYSTEM_DB_URL, connect_args={"check_same_thread": False})
    SystemBase.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="session")
def tenant_engine():
    """
    Create a single in-memory tenant database engine for the test session.
    All tenants will share this same physical DB in tests, effectively separate schema instances
    are simulated by just using the same tables. This assumes tests don't need strict
    table-level isolation between orgs within the same test function.
    """
    engine = create_engine(TENANT_DB_URL, connect_args={"check_same_thread": False})
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
def mock_tenant_engine(monkeypatch, tenant_engine):
    """
    Patch get_tenant_engine to always return our in-memory engine.
    This intercepts all backend.database.get_tenant_session calls.
    """
    def mock_get_engine(org_id):
        # We ignore org_id and return the same global test engine
        return tenant_engine
    
    monkeypatch.setattr("backend.database.get_tenant_engine", mock_get_engine)

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
def clean_db(tenant_engine):
    """
    Clean the tenant database after each test.
    Since tests share the same in-memory DB engine and application code commits transactions,
    we need to explicitly truncate tables to prevent state leakage.
    """
    yield
    
    # Truncate all tables
    from sqlalchemy import inspect, text
    inspector = inspect(tenant_engine)
    with tenant_engine.begin() as conn:
        for table in inspector.get_table_names():
            conn.execute(text(f"DELETE FROM {table}"))
