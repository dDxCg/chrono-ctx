import threading

from vcs.shared.types import SourceEvent, MovedEvent, ModifiedEvent, DeletedEvent, CreatedEvent
from vcs.services.versioning import moved_handle, modified_handle, deleted_handle, created_handle
from vcs.db.sqlite import DBHandler
from vcs.shared.temp_file import TempFile
from vcs.workers.local.local_queue import LocalQueue

from utils.helper import get_db_url
from utils.logger import log_enabled
from vcs.workers.local.utils import STOP


class LocalConsumer:
    def __init__(self, db_handler: DBHandler):
        self.db_handler = db_handler

    @log_enabled
    def handle(self, event: SourceEvent):
        if isinstance(event, MovedEvent):
            moved_handle(self.db_handler, event)
        if isinstance(event, ModifiedEvent):
            modified_handle(self.db_handler, event, tmp_file=TempFile.from_path(event.src))
        if isinstance(event, DeletedEvent):
            deleted_handle(self.db_handler, event)
        if isinstance(event, CreatedEvent):
            created_handle(self.db_handler, event)
        
        
class LocalConsumerWorker(threading.Thread):
    def __init__(self, stop_event):
        super().__init__()
        self.queue = LocalQueue()
        self.stop_event = stop_event

    def run(self):
        db = DBHandler.from_url(get_db_url())
        self.consumer = LocalConsumer(db_handler=db)
        while True:
            event = self.queue.consume()

            if event is STOP:
                self.queue.close()
                break

            self.consumer.handle(event)




