from pathlib import Path


from src.utils.helper import collect_files, hash, gen_ulid, _path_normalize
from src.utils.logger import log_enabled

from src.vcs.shared.config import BLOB_ROOT
from src.vcs.shared.types import ContextEntry
from src.vcs.db.sqlite import DBHandler
from src.vcs.services.versioning import append_context

class LocalAdapter:
    def __init__(self, db_handler: DBHandler):
        self.db_handler = db_handler

    def local_file_processing(self, file_path: Path):
        file_content = file_path.read_bytes()
        content_hash = hash(file_content)
        context_id = gen_ulid()

        context_entry = ContextEntry(
            context_id=context_id,
            provider="local",
            location=_path_normalize(file_path),
            content_hash=content_hash
        )

        append_context(self.db_handler, context_entry)
        save_path = BLOB_ROOT / f"{content_hash}.blob"
        save_path.write_bytes(file_content)

    def local_directory_processing(self, dir_path):
        files = collect_files(dir_path)
        for file_path in files:
            self.local_file_processing(file_path)

    @log_enabled
    def local_processing(self, path):
        p = Path(path).resolve()

        if p.is_file():
            self.local_file_processing(path)

        if p.is_dir():
            self.local_directory_processing(path)


