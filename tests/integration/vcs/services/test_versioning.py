from vcs.services.versioning import sync_source
from tests.fixtures.seed import Seeder
from vcs.db.sqlite import DBHandler
from vcs.shared.types import Query
from unittest.mock import patch

class TestSyncSourceStatus:
    def test_empty_sources(
        self,
        db_handler: DBHandler,
        seeder: Seeder
    ):
        seeder.seed_locations()

        sync_source(
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
            

    def test_selected_sources(
        self,
        db_handler: DBHandler,
        seeder: Seeder
    ):
        seeder.seed_locations()

        with patch(
            "src.vcs.services.versioning.path_normalize",
            return_value="/root"
        ), patch(
            "src.vcs.services.versioning.collect_files",
            return_value=[
                "/root/a",
                "/root/b",
            ]
        ):
            sync_source(
                db_handler,
                [
                    {"path": "/root"}
                ]
            )

        rows = db_handler.execute(
            Query(
                query="""
                    SELECT location, status
                    FROM locations
                    ORDER BY location
                """
            ),
            commit=False
        )

        result = {
            location: status
            for location, status in rows
        }

        assert result["/root"] == 0
        assert result["/root/a"] == 1
        assert result["/root/b"] == 1
        assert result["/other"] == 0
    