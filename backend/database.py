import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import PROJECT_ROOT

logger = logging.getLogger(__name__)

# Base classes for separate schemas
SystemBase = declarative_base()
TenantBase = declarative_base()

# --- System Database ---
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

SYSTEM_DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'system.db')}"

system_engine = create_engine(
    SYSTEM_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for FastAPI threading
)

SystemSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=system_engine)


def get_system_db():
    """Dependency for System DB (Users/Orgs)"""
    db = SystemSessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Tenant Database Router ---

# Cache engines to avoid recreating them per request
# Key: org_id, Value: engine
_tenant_engines = {}


def get_tenant_engine(org_id: str):
    """
    Get or create an engine for a specific tenant.
    Ensures the directory exists.
    """
    if org_id in _tenant_engines:
        return _tenant_engines[org_id]

    # Path: data/organizations/{org_id}/tenant.db
    org_dir = os.path.join(DATA_DIR, "organizations", org_id)
    os.makedirs(org_dir, exist_ok=True)

    db_path = os.path.join(org_dir, "tenant.db")
    db_url = f"sqlite:///{db_path}"

    logger.info(f"Connecting to tenant DB: {db_url}")

    engine = create_engine(db_url, connect_args={"check_same_thread": False})

    # Cache it
    _tenant_engines[org_id] = engine

    # Note: Migrations are applied in get_tenant_session to ensure
    # proper sequencing with create_all()

    return engine


def get_tenant_session(org_id: str):
    """
    Get a session for a specific tenant.
    Auto-creates tables if they don't exist and applies migrations.
    """
    engine = get_tenant_engine(org_id)

    from sqlalchemy import inspect

    from .tenant_migrations import apply_tenant_migrations, set_version

    # Check if DB is fresh (no conversation table)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    is_fresh_db = "conversations" not in existing_tables

    # Ensure tables exist (Lazy Migration)
    # This creates the schema as defined in models.py (which is Latest)
    # IMPORTANT: Must import models here to ensure they are registered with ValidBase/TenantBase
    TenantBase.metadata.create_all(bind=engine)

    if is_fresh_db:
        # If we just created the DB, we are effectively at the latest schema version.
        # We implicitly skip all migrations that are "catch-up" for existing/legacy DBs.
        # Currently, latest migration is 2.
        logger.info("Initialized fresh Tenant DB. Setting version to 2.")
        set_version(engine, 2)
    else:
        # Existing DB: Apply standard migrations
        apply_tenant_migrations(engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
