from unittest.mock import MagicMock, patch
from src.vcs.services.versioning import deactive_and_reactive_sources

class TestSyncSourceStatus:
    @patch("src.vcs.services.versioning.collect_files")
    @patch("src.vcs.services.versioning.path_normalize")
    def test_selected_sources(self, mock_normalize, mock_collect):
        db_handler = MagicMock()

        sources = [
            {"path": "/tmp/source1"}
        ]

        mock_normalize.return_value = "/normalized/source1"
        mock_collect.return_value = [
            "/normalized/source1/file1.py",
            "/normalized/source1/file2.py",
        ]

        deactive_and_reactive_sources(db_handler, sources)

        db_handler.begin.assert_called_once()
        db_handler.commit.assert_called_once()
        db_handler.rollback.assert_not_called()

        calls = db_handler.execute.call_args_list
        
        # deactivate all
        assert calls[0].args[0].query == \
            "UPDATE locations SET status = 0"

        # reactivate file1
        assert calls[1].args[0].query == \
            "UPDATE locations SET status = 1 WHERE location = ?"
        assert calls[1].args[0].params == (
            "/normalized/source1/file1.py",
        )

        # reactivate file2
        assert calls[2].args[0].query == \
            "UPDATE locations SET status = 1 WHERE location = ?"
        assert calls[2].args[0].params == (
            "/normalized/source1/file2.py",
        )

    @patch("src.vcs.services.versioning.collect_files")
    @patch("src.vcs.services.versioning.path_normalize")
    def test_rollback_on_error(self, mock_normalize, mock_collect):
        db_handler = MagicMock()

        sources = [{"path": "/tmp/source1"}]

        mock_normalize.return_value = "/normalized/source1"
        mock_collect.side_effect = Exception("collect failed")

        try:
            deactive_and_reactive_sources(db_handler, sources)
            assert False, "Exception should be raised"
        except Exception:
            pass

        db_handler.begin.assert_called_once()
        db_handler.rollback.assert_called_once()
        db_handler.commit.assert_not_called()

    @patch("src.vcs.services.versioning.collect_files")
    @patch("src.vcs.services.versioning.path_normalize")
    def test_multiple_sources(self, mock_normalize, mock_collect):
        db_handler = MagicMock()

        sources = [
            {"path": "/tmp/a"},
            {"path": "/tmp/b"},
        ]

        mock_normalize.side_effect = [
            "/normalized/a",
            "/normalized/b",
        ]

        mock_collect.side_effect = [
            ["/normalized/a/f1.py"],
            ["/normalized/b/f2.py", "/normalized/b/f3.py"],
        ]

        deactive_and_reactive_sources(db_handler, sources)

        # 1 deactivate + 3 reactive updates
        assert db_handler.execute.call_count == 4
        db_handler.commit.assert_called_once()