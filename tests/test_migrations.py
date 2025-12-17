import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from backend.tenant_migrations import apply_tenant_migrations, get_current_version

# --- System DB Tests (Alembic) ---


@pytest.fixture
def alembic_config():
    """Return Alembic configuration."""
    # Assume we are running from project root
    config = Config("alembic.ini")
    return config


def test_alembic_upgrade_downgrade(alembic_config, tmp_path):
    """
    Test that we can upgrade to head and downgrade.
    """
    # Create a temp DB file
    db_file = tmp_path / "test_system.db"
    db_url = f"sqlite:///{db_file}"

    # Set env var for env.py to pick up
    os.environ["ALEMBIC_DB_URL"] = db_url

    try:
        # Override URL in config object as well (though env.py runs independently)
        alembic_config.set_main_option("sqlalchemy.url", db_url)

        # 1. Upgrade to head
        command.upgrade(alembic_config, "head")

        # Verify tables exist
        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "users" in tables
        assert "organizations" in tables
        assert "alembic_version" in tables
        # Legacy tables should NOT be there (since we apply all including drop)
        assert "conversations" not in tables

        # 2. Downgrade to base
        command.downgrade(alembic_config, "base")

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "users" not in tables
        assert "organizations" not in tables
    finally:
        # Cleanup
        if "ALEMBIC_DB_URL" in os.environ:
            del os.environ["ALEMBIC_DB_URL"]


# --- Tenant DB Tests ---


def test_tenant_migrations_fresh_install():
    """Test applying migrations to a fresh DB initialized with create_all."""
    engine = create_engine("sqlite:///:memory:")

    # Simulate a new tenant creation: create_all is called using LATEST schema
    from backend.models import TenantBase

    TenantBase.metadata.create_all(engine)

    # Pre-condition: Table exists AND column exists (because model has it)
    inspector = inspect(engine)
    assert "conversations" in inspector.get_table_names()
    columns = [c["name"] for c in inspector.get_columns("conversations")]
    assert "processing_state" in columns

    # Initial version is 0 because we just created it (unless we set it in creation flow, which we likely don't yet)
    version = get_current_version(engine)
    assert version == 0

    # Run migrations
    # Expectation: Logic detects column exists, sets version to 1, skips ALTER TABLE
    apply_tenant_migrations(engine)

    # Verify version 1
    version = get_current_version(engine)
    assert version == 1


def test_tenant_migrations_legacy_upgrade():
    """Test upgrading a legacy DB (version 0) to version 1."""
    engine = create_engine("sqlite:///:memory:")

    # Setup legacy state: Table exists, but no column
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE conversations (id TEXT PRIMARY KEY)"))
        # No processing_state column
        conn.execute(text("PRAGMA user_version = 0"))

    version = get_current_version(engine)
    assert version == 0

    # Apply migrations
    apply_tenant_migrations(engine)

    # Verify version 1
    version = get_current_version(engine)
    assert version == 1

    # Verify column exists
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("conversations")]
    assert "processing_state" in columns


def test_tenant_migrations_legacy_idempotency():
    """Test upgrading a legacy DB that ALREADY has the column (pseudo-v1 but v0 in pragma due to ad-hoc run)."""
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as conn:
        conn.execute(
            text("CREATE TABLE conversations (id TEXT PRIMARY KEY, processing_state VARCHAR)")
        )
        conn.execute(text("PRAGMA user_version = 0"))

    # Apply migrations
    # Detailed log logic should detect column and fast-forward version
    apply_tenant_migrations(engine)

    version = get_current_version(engine)
    assert version == 1

    # Verify we didn't try to add it again (which would fail in sqlite usually or succeed if defensive)
    # The code logic specifically checks for this.
