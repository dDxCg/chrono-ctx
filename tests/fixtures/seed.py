from src.vcs.db.sqlite import DBHandler
from src.vcs.shared.types import Query

class Seeder:

    BASIC_CONTEXTS = [
        ("ctx0",),
        ("ctx1",),
        ("ctx2",),
        ("ctx3",),
    ]

    BASIC_LOCATIONS = [
            ("/root", "ctx0", 1),
            ("/root/a", "ctx1", 1),
            ("/root/b", "ctx2", 1),
            ("/other", "ctx3", 1),
        ]

    BASIC_VERSIONS = [
        (1, "ctx0", "hash0"),
        (2, "ctx0", "hash1"),
        (1, "ctx1", "hash2"),
        (1, "ctx2", "hash3"),
        (1, "ctx3", "hash4"),
    ]

    def __init__(self, db_handler: DBHandler):
        self.db_handler = db_handler

    def seed_locations(self, rows=None):
        rows = rows or self.BASIC_LOCATIONS

        for location, context_id, status in rows:
            self.db_handler.execute(
                Query(
                    """
                    INSERT INTO locations(
                        location,
                        context_id,
                        status
                    )
                    VALUES (?, ?, ?)
                    """,
                    (location, context_id, status)
                )
            )

    def seed_versions(self, rows=None):
        rows = rows or self.BASIC_VERSIONS

        for version, context_id, content_hash in rows:
            self.db_handler.execute(
                Query(
                    """
                    INSERT INTO versions(
                        version_number,
                        context_id,
                        content_hash
                    )
                    VALUES (?, ?, ?)
                    """,
                    (version, context_id, content_hash)
                )
            )

    def seed_contexts(self, rows=None):
        rows = rows or self.BASIC_CONTEXTS

        for (context_id,) in rows:
            self.db_handler.execute(
                Query(
                    """
                    INSERT INTO contexts(
                        context_id
                    )
                    VALUES (?)
                    """,
                    (context_id)
                )
            )

    def seed_db(self, ctx_rows=None, loc_rows=None, ver_rows=None):
        self.seed_contexts(self, ctx_rows)
        self.seed_locations(self, loc_rows)
        self.seed_versions(self, ver_rows)