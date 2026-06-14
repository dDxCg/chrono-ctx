from src.vcs.services.versioning import deactive_and_reactive_sources
from tests.fixtures.seed import Seeder
from src.vcs.db.sqlite import DBHandler
from src.vcs.shared.types import Query

class TestSyncSourceStatus:
    def test_reactive_selected_sources(
        self,
        db_handler: DBHandler,
        seeder: Seeder
    ):
        seeder.seed_locations()

        deactive_and_reactive_sources(
            db_handler,
            ["/root"]
        )

        rows = db_handler.execute(
            Query(
                query = "SELECT location, status FROM locations ORDER BY location"
            ),
            commit=False
        )

        result = {
            location: status
            for location, status in rows
        }

        assert result["/root"] == 1
        assert result["/root/a"] == 1
        assert result["/root/b"] == 1

        assert result["/other"] == 0

    def test_multiple_sources(
        self,
        db_handler: DBHandler,
        seeder: Seeder
    ):
        seeder.seed_locations()

        db_handler.execute(
            Query(
                query = "INSERT INTO locations(location, context_id, status) VALUES (?, ?, ?)",
                params = ("/project", "ctx4", 0)
            )
        )

        deactive_and_reactive_sources(
            db_handler,
            [
                "/root",
                "/project"
            ]
        )

        rows = db_handler.execute(
            Query(
                query = "SELECT location, status FROM locations"
            ),
            commit=False
        )

        result = dict(rows)

        assert result["/root"] == 1
        assert result["/root/a"] == 1
        assert result["/root/b"] == 1
        assert result["/project"] == 1

        assert result["/other"] == 0

    def test_empty_sources(
        self,
        db_handler: DBHandler,
        seeder: Seeder
    ):
        seeder.seed_locations()

        deactive_and_reactive_sources(
            db_handler,
            []
        )

        rows = db_handler.execute(
            Query(
                query="SELECT status FROM locations"
            ),
            commit=False
        )

        assert all(
            status == 0
            for (status,) in rows
        )
            

    