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

    # Apply standardized migrations on connect
    from .tenant_migrations import apply_tenant_migrations

    apply_tenant_migrations(engine)

    return engine


def get_tenant_session(org_id: str):
    """
    Get a session for a specific tenant.
    Auto-creates tables if they don't exist (simplistic migration for now).
    """
    engine = get_tenant_engine(org_id)

    # Ensure tables exist (Lazy Migration)
    # in prod, we might want to do this explicitly, but for now this ensures
    # new tenant DBs are initialized.
    # IMPORTANT: Must import models here to ensure they are registered with ValidBase/TenantBase

    TenantBase.metadata.create_all(bind=engine)

    # Run schema migrations for existing databases
    # Run schema migrations for existing databases
    from .tenant_migrations import apply_tenant_migrations

    apply_tenant_migrations(engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
