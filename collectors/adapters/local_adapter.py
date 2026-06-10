from pathlib import Path
import hashlib
import uuid

from utils.helper import save_to_file
from utils.logger import log_enabled

from collectors.shared.config import BLOB_ROOT
from collectors.shared.types import ContextEntry
from collectors.db_handler import DBHandler
from collectors.shared.functions import append_context

class LocalAdapter:
    def __init__(self, db_handler: DBHandler):
        self.db_handler = db_handler

    @log_enabled("Process local file")
    def local_file_processing(self, file_path):
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
        save_to_file(file_content, BLOB_ROOT / f"{content_hash}.blob")
    
    
    




