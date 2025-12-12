
import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_PATH = "../shared-data/databases/providers.db"
CASES_DB_PATH = "../shared-data/databases/cases.db"

@contextmanager
def get_db_connection():
    """Yields a SQLite connection."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row # Access columns by name
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise e
    finally:
        if conn:
            conn.close()

def init_db():
    """Initializes the database schema if it doesn't exist."""
    # Schema creation is handled by the migration script for now, 
    # but we can add 'CREATE TABLE IF NOT EXISTS' here for safety.
    pass
