"""Alembic environment configuration for async SQLAlchemy."""

import asyncio
import re
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from alembic.script import ScriptDirectory

# Import Base and all models for autogenerate support
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.base import Base

# Import all models to ensure they're registered with Base.metadata
from src.adapters.persistence import models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get database URL from settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.async_database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def get_next_sequential_revision():
    """Get the next sequential revision number by scanning existing migrations.

    Scans all migration files in the versions directory and finds the highest
    numeric revision ID, then returns the next one formatted as 4-digit zero-padded.

    Returns:
        str: Next sequential revision ID (e.g., "0001", "0002", etc.)
    """
    script_dir = ScriptDirectory.from_config(config)
    versions_dir = Path(script_dir.versions)

    max_revision = 0

    # Scan all Python files in versions directory
    for file in versions_dir.glob("*.py"):
        if file.name.startswith("__"):
            continue
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for revision = "..." or revision: str = "..."
                # Match both quoted strings and numeric-only IDs (4+ digits for sequential)
                # Pattern matches: revision = "0001" or revision: str = '0001'
                match = re.search(
                    r'revision\s*[=:]\s*["\'](\d{4,})["\']',
                    content
                )
                if match:
                    rev_id = match.group(1)
                    # Only consider pure numeric IDs (sequential ones)
                    if rev_id.isdigit():
                        rev_num = int(rev_id)
                        max_revision = max(max_revision, rev_num)
        except Exception:
            # Skip files that can't be read or parsed
            pass

    return f"{max_revision + 1:04d}"  # Returns "0001", "0002", etc.


def process_revision_directives(context, revision, directives):
    """Customize revision ID generation to use sequential numbers.

    This hook is called by Alembic when generating new revision scripts.
    If sequential revisions are enabled in config, it replaces the auto-generated
    revision ID with a sequential numeric one.

    Args:
        context: Alembic migration context
        revision: Tuple of (revision_id, branch_labels) or None
        directives: List of revision directive objects
    """
    use_sequential = config.get_main_option(
        "use_sequential_revisions", "true"
    ).lower() == "true"

    if use_sequential and directives:
        # Check if we should override the revision ID
        # Override if:
        # 1. No explicit --rev-id was provided (revision is None or has auto-generated hash)
        # 2. The current rev_id doesn't look like a sequential number (4+ digits)
        current_rev_id = directives[0].rev_id if directives else None

        if current_rev_id:
            # If it's already a sequential number (4+ digits), don't override
            if current_rev_id.isdigit() and len(current_rev_id) >= 4:
                return
            # If it looks like a hash (alphanumeric, not all digits), override it
            if not current_rev_id.isdigit():
                new_rev_id = get_next_sequential_revision()
                directives[0].rev_id = new_rev_id
        else:
            # No rev_id set yet, generate sequential one
            new_rev_id = get_next_sequential_revision()
            directives[0].rev_id = new_rev_id


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection.

    Args:
        connection: SQLAlchemy connection
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async engine."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
