from unittest.mock import Mock, call
import pytest
from src.vcs.services.versioning import deactive_and_reactive_sources

class TestSyncSourceStatus:
    def test_success(self):
        db = Mock()

        sources = [
            "/tmp/a",
            "/tmp/b"
        ]

        deactive_and_reactive_sources(
            db_handler=db,
            sources=sources
        )

        db.begin.assert_called_once()
        db.commit.assert_called_once()
        db.rollback.assert_not_called()

        assert db.execute.call_count == 3

    def test_transaction_order(self):
        db = Mock()

        deactive_and_reactive_sources(
            db,
            ["/tmp/a"]
        )

        assert db.mock_calls[0] == call.begin()
        assert db.mock_calls[-1] == call.commit()

    def test_query_parameter(self):
        db = Mock()

        deactive_and_reactive_sources(
            db,
            ["/root"]
        )

        reactive_query = db.execute.call_args_list[1].args[0]

        assert reactive_query.params == (
            "/root",
            "/root/%"
        )

    def test_rollback_when_execute_fail(self):
        db = Mock()

        db.execute.side_effect = [
            None,
            Exception("DB Error")
        ]

        with pytest.raises(Exception):
            deactive_and_reactive_sources(
                db,
                ["/tmp/a"]
            )

        db.begin.assert_called_once()
        db.rollback.assert_called_once()
        db.commit.assert_not_called()