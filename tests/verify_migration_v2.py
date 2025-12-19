import logging
import os
import sys

from sqlalchemy import create_engine, inspect, text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.tenant_migrations import apply_tenant_migrations, get_current_version

# Configure logging
logging.basicConfig(level=logging.INFO)


def test_migration():
    db_path = "test_migration_v2.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)

    print(f"Creating test DB at {db_path}...")

    # 1. Setup V1 State (Manually)
    # This simulates a DB that has Migration 1 applied
    with engine.begin() as conn:
        conn.execute(text("PRAGMA user_version = 1"))
        conn.execute(
            text("""
            CREATE TABLE conversations (
                id VARCHAR PRIMARY KEY,
                processing_state VARCHAR DEFAULT 'idle'
            )
        """)
        )

    print("Initialized DB at Version 1.")

    # 2. Apply migrations (Should trigger Migration 2)
    print("Applying migrations...")
    apply_tenant_migrations(engine)

    # 3. Check version
    version = get_current_version(engine)
    print(f"Current DB Version: {version}")
    assert version >= 2, f"Expected version >= 2, got {version}"

    # 4. Check tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables found: {tables}")

    expected_tables = ["council_packs", "council_configuration"]
    for t in expected_tables:
        assert t in tables, f"Missing table: {t}"
        print(f"Verified {t} exists.")

    # 5. Check schema of council_configuration
    columns = {c["name"]: c for c in inspector.get_columns("council_configuration")}
    assert "user_id" in columns
    assert "active_pack_id" in columns
    assert columns["user_id"]["primary_key"] == 1
    print("council_configuration schema verified.")

    # Cleanup
    os.remove(db_path)
    print("Test passed and DB cleaned up.")


if __name__ == "__main__":
    try:
        test_migration()
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
