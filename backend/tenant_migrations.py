import logging

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)

# Migration Definitions
# Format: (version_id, description, sql_command_or_callable)
# Note: For SQLite, some ALTER TABLE commands must be run specifically.
TENANT_MIGRATIONS = [
    (
        1,
        "add_processing_state_to_conversations",
        """
        ALTER TABLE conversations ADD COLUMN processing_state VARCHAR DEFAULT 'idle';
        UPDATE conversations SET processing_state = 'idle' WHERE processing_state IS NULL;
        """,
    ),
    (
        2,
        "add_council_packs_and_config",
        """
        CREATE TABLE council_packs (
            id VARCHAR PRIMARY KEY,
            display_name VARCHAR NOT NULL,
            description TEXT,
            config_json TEXT NOT NULL,
            is_system BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE council_configuration (
            user_id VARCHAR PRIMARY KEY,
            active_pack_id VARCHAR,
            active_personalities_json TEXT,
            active_strategy_id VARCHAR,
            active_system_prompts_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
    ),
    (
        3,
        "add_consensus_strategies_table",
        """
        CREATE TABLE consensus_strategies (
            id VARCHAR PRIMARY KEY,
            display_name VARCHAR NOT NULL,
            description TEXT,
            prompt_content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
    ),
]


def get_current_version(engine):
    """Get the current user_version of the SQLite database."""
    with engine.connect() as conn:
        # PRAGMA user_version is a standard SQLite mechanism for versioning
        result = conn.execute(text("PRAGMA user_version")).scalar()
        return int(result)


def set_version(engine, version):
    """Set the user_version of the SQLite database."""
    with engine.begin() as conn:
        conn.execute(text(f"PRAGMA user_version = {version}"))


def apply_tenant_migrations(engine):
    """
    Apply pending migrations to valuable tenant database.
    This uses SQLite `user_version` PRAGMA to track state.
    """
    current_ver = get_current_version(engine)

    # Pre-check for legacy schema state (the 'processing_state' column might exist
    # from previous ad-hoc migration but version is 0)
    # If version is 0, we should inspect to see if we need to skip migration 1
    if current_ver == 0:
        inspector = inspect(engine)
        if "conversations" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("conversations")]
            if "processing_state" in columns:
                logger.info(
                    "Detected legacy schema with 'processing_state'. Fast-forwarding version to 1."
                )
                set_version(engine, 1)
                current_ver = 1

    logger.info(f"Current Tenant DB Version: {current_ver}")

    for version, name, operation in TENANT_MIGRATIONS:
        if current_ver < version:
            logger.info(f"Applying migration {version}: {name}")
            try:
                with engine.begin() as conn:
                    # Split multiple statements if necessary (SQLite driver usually handles one at a time)
                    statements = [s.strip() for s in operation.split(";") if s.strip()]
                    for stmt in statements:
                        conn.execute(text(stmt))

                # Update version AFTER successful transaction
                set_version(engine, version)
                current_ver = version
                logger.info(f"Successfully applied migration {version}")
            except Exception as e:
                logger.error(f"Migration {version} failed: {e}")
                raise e
