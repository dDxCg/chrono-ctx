from pathlib import Path
import hashlib
import uuid

from utils.helper import save_to_file, path_normalize, collect_files
from utils.logger import log_enabled

from collectors.shared.config import BLOB_ROOT
from collectors.shared.types import ContextEntry
from app.db_handler import DBHandler
from collectors.shared.functions import append_context

class LocalAdapter:
    def __init__(self, db_handler: DBHandler):
        self.db_handler = db_handler

    @log_enabled("Process local file")
    def local_file_processing(self, file_path):
        file_path = path_normalize(file_path)
        with open(file_path, "rb") as f:
            file_content = f.read()

        content_hash = hashlib.sha256(file_content).hexdigest()
        context_id = str(uuid.uuid4())

        context_entry = ContextEntry(
            context_id=context_id,
            provider="local",
            location=file_path,
            content_hash=content_hash
        )

        append_context(self.db_handler, context_entry)
        save_to_file(file_content, BLOB_ROOT / f"{content_hash}.blob", mode="wb")

    @log_enabled
    def local_directory_processing(self, dir_path):
        dir_path = path_normalize(dir_path)
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


