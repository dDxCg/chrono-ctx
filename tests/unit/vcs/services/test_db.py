import sqlite3

from vcs.db.sqlite import DBHandler
from vcs.services.db import init_db
from vcs.shared.types import Query


def test_ac3_init_db_applies_schema_regardless_of_cwd(monkeypatch, tmp_path):
    """The actual bug (spec 030): init_db() used to build its own raw,
    un-anchored 'data/schema.sql' path instead of calling get_schema_path()
    - it only ever worked because every real invocation happened to run
    from the repo root. Running from an unrelated cwd is what catches it."""
    monkeypatch.chdir(tmp_path)

    db_handler = DBHandler(conn=sqlite3.connect(":memory:"))
    try:
        init_db(db_handler)

        tables = db_handler.execute(
            Query("SELECT name FROM sqlite_master WHERE type = 'table'"), commit=False
        )
        table_names = {row[0] for row in tables}
        assert "contexts" in table_names
        assert "locations" in table_names
    finally:
        db_handler.close()


def _columns(db_handler, table):
    rows = db_handler.execute(Query(f"PRAGMA table_info({table})"), commit=False)
    return {row[1] for row in rows}


def test_ac1_fresh_db_locations_has_device_id_column(monkeypatch, tmp_path):
    """Spec 041: locations' primary key becomes (device_id, st_ino, st_dev)
    on a database that has never been initialized before."""
    monkeypatch.chdir(tmp_path)

    db_handler = DBHandler(conn=sqlite3.connect(":memory:"))
    try:
        init_db(db_handler)

        assert "device_id" in _columns(db_handler, "locations")
    finally:
        db_handler.close()


def test_ac3_ec1_init_db_migrates_pre_041_locations_table_without_raising(monkeypatch, tmp_path):
    """A database created before spec 041 has locations with no device_id
    column and PK(st_ino, st_dev). CREATE TABLE IF NOT EXISTS is a silent
    no-op against it, so init_db() must detect and rebuild it explicitly -
    and must not misfire on a database with no locations table at all yet
    (the fresh-install case, exercised by the AC-1 test above)."""
    monkeypatch.chdir(tmp_path)

    db_handler = DBHandler(conn=sqlite3.connect(":memory:"))
    try:
        db_handler.conn.executescript("""
            CREATE TABLE locations (
                st_ino TEXT,
                st_dev TEXT,
                context_id INTEGER,
                location TEXT,
                provider TEXT,
                status INTEGER DEFAULT 1,
                PRIMARY KEY(st_ino, st_dev)
            );
        """)

        init_db(db_handler)  # must not raise

        assert "device_id" in _columns(db_handler, "locations")
    finally:
        db_handler.close()


def test_ac4_migration_preserves_contexts_and_versions_rows(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    db_handler = DBHandler(conn=sqlite3.connect(":memory:"))
    try:
        db_handler.conn.executescript("""
            CREATE TABLE contexts (context_id TEXT PRIMARY KEY, created_at DATETIME);
            CREATE TABLE versions (
                version_number INTEGER, context_id INTEGER, content_hash TEXT,
                created_at DATETIME, PRIMARY KEY(version_number, context_id)
            );
            CREATE TABLE locations (
                st_ino TEXT, st_dev TEXT, context_id INTEGER, location TEXT,
                provider TEXT, status INTEGER DEFAULT 1, PRIMARY KEY(st_ino, st_dev)
            );
            INSERT INTO contexts (context_id) VALUES ('ctx-survives');
            INSERT INTO versions (version_number, context_id, content_hash) VALUES (1, 'ctx-survives', 'deadbeef');
        """)

        init_db(db_handler)

        contexts = db_handler.execute(Query("SELECT context_id FROM contexts"), commit=False)
        versions = db_handler.execute(Query("SELECT context_id FROM versions"), commit=False)
        assert contexts == [("ctx-survives",)]
        assert versions == [("ctx-survives",)]
    finally:
        db_handler.close()
