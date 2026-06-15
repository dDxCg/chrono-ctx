from pathlib import Path
import sqlite3
import pytest
from src.vcs.db.sqlite import DBHandler
from tests.fixtures.seed import Seeder

@pytest.fixture
def db_handler():
    conn = sqlite3.connect(":memory:")

    schema = Path(
        "tests/fixtures/schema.sql"
    ).read_text()

    conn.executescript(schema)

    yield DBHandler(conn=conn)

    conn.close()

@pytest.fixture
def seeder(db_handler):
    return Seeder(db_handler)


