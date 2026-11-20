"""SQLite connection handling, schema creation and seeding.

[Unit II] highlights:
  * File Management - reads schema.sql with a context manager, deletes the
    .db file on reset with os.remove;
  * Exceptions      - sqlite3 errors are raised with context; the
    get_db() context manager always commits on success and rolls back +
    closes on failure (try / except / finally);
  * Modules/Packages - this is one module inside the ``database`` package.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import SETTINGS
from database import seed_data
from utils.app_logger import get_logger

_BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = _BASE_DIR / "schema.sql"

# Path of the .db file currently in use (tests override this with a temp file)
_db_path = None

logger = get_logger("database")


def configure_database(path):
    """Point the module at a specific database file (used by the tests)."""
    global _db_path
    _db_path = str(path)


def get_db_path():
    """Return the database file path currently in use."""
    return _db_path or SETTINGS["database_path"]


def connect():
    """Open a connection with row factory and FK enforcement enabled."""
    path = get_db_path()
    try:
        conn = sqlite3.connect(path)
    except sqlite3.Error as error:
        raise RuntimeError(f"Could not open database '{path}': {error}") from error
    conn.row_factory = sqlite3.Row        # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")  # enforce FKs on every connection
    return conn


@contextmanager
def get_db():
    """Yield a connection; commit on success, rollback on any error.

    A context manager guarantees the connection is ALWAYS closed
    (the finally block), no matter what happens inside the with block.
    """
    conn = connect()
    try:
        yield conn
        conn.commit()                    # success -> save the changes
    except Exception:
        conn.rollback()                  # failure -> undo everything
        raise                            # re-raise so callers see the error
    finally:
        conn.close()                     # always runs, even after raise


def init_db(seed=True, force=False):
    """Create the schema (and optionally seed the sample data).

    With ``force=True`` an existing database file is deleted first,
    giving a completely fresh start.
    """
    path = get_db_path()

    if force and os.path.exists(path):
        os.remove(path)                  # [Unit II] file deletion
        logger.warning("Existing database deleted (%s)", path)

    conn = connect()
    try:
        # [Unit II] File Management: reading the schema from a .sql file
        with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
            conn.executescript(schema_file.read())
        if seed:
            seed_database(conn)
        conn.commit()
    finally:
        conn.close()


def seed_database(conn=None):
    """Insert the case-study sample rows (skips tables that already have data)."""
    owns_connection = conn is None
    conn = conn or connect()
    try:
        for table_name, columns, rows in seed_data.SEED_TABLES:
            existing = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            if existing:                 # already seeded -> skip (idempotent)
                continue
            if not rows:
                continue
            placeholders = ", ".join("?" * len(columns))
            column_list = ", ".join(columns)
            conn.executemany(
                f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})",
                rows,
            )
            logger.info("Seeded %d rows into %s", len(rows), table_name)
    finally:
        if owns_connection:
            conn.commit()
            conn.close()


def reset_db():
    """Delete, recreate and reseed the database in one call."""
    init_db(seed=True, force=True)
    logger.warning("Database was reset and reseeded")


def table_row_counts():
    """Row count per table - used by /api/health and the summary report."""
    counts = {}
    conn = connect()
    try:
        for table_name in seed_data.ALL_TABLES:
            counts[table_name] = conn.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]
    finally:
        conn.close()
    return counts
