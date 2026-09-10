from pathlib import Path

from utils.helper import get_db_url, get_schema_path
from vcs.db.sqlite import DBHandler
from vcs.shared.types import Query


def _migrate_locations_table_if_needed(db_handler: DBHandler) -> None:
    """locations predates device_id/the (device_id, st_ino, st_dev)
    primary key (spec 041). `CREATE TABLE IF NOT EXISTS` is a silent
    no-op against a table that already exists in the old shape, so an
    upgrade needs this explicit step. Safe to just drop and let
    schema.sql recreate empty: locations is re-derivable bookkeeping,
    not user content - the git mirror history it points at is keyed by
    path, not by this table, and is untouched either way (spec 041's
    "existing-row impact" section).

    A database with no locations table yet (fresh install) must not be
    misread as "old shape" - PRAGMA table_info on a nonexistent table
    simply returns no rows, so `columns` is empty and this is a no-op."""
    columns = {
        row[1]
        for row in db_handler.execute(Query("PRAGMA table_info(locations)"), commit=False)
    }
    if columns and "device_id" not in columns:
        db_handler.execute(Query("DROP TABLE locations"))


def init_db(db_handler: DBHandler):
    db_path = Path(get_db_url())
    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.touch(exist_ok=True)

    _migrate_locations_table_if_needed(db_handler)
    db_handler.execute_script(get_schema_path())

def reset_db(db_handler: DBHandler):
    db_path = Path(get_db_url())
    if db_path.is_file():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.touch(exist_ok=True)
    init_db(db_handler)
    

    

    
    