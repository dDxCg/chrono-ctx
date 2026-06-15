from src.vcs.shared.types import SourceEvent, MovedEvent, ModifiedEvent, DeletedEvent, CreatedEvent
from src.vcs.services.versioning import moved_handle, modified_handle, deleted_handle, created_handle
from src.vcs.db.sqlite import DBHandler
from src.vcs.shared.temp_file import TempFile
from src.vcs.workers.local.local_queue import LocalQueue

from threading import Thread

STOP = object()

class LocalConsumer:
    def __init__(self, db_handler: DBHandler):
        self.db_handler = db_handler

    def handle(self, event: SourceEvent):
        if isinstance(event, MovedEvent):
            moved_handle(self.db_handler, event)
        if isinstance(event, ModifiedEvent):
            modified_handle(self.db_handler, event, tmp_file=TempFile.from_path(event.src))
        if isinstance(event, DeletedEvent):
            deleted_handle(self.db_handler, event)
        if isinstance(event, CreatedEvent):
            created_handle(self.db_handler, event)



class ConsumerWorker(Thread):
    def __init__(self, queue: LocalQueue, consumer: LocalConsumer):
        super().__init__(daemon=True)
        self.queue = queue
        self.consumer = consumer

    def run(self):
        while True:
            event = self.queue.consume()

            if event is STOP:
                break

            self.consumer.handle(event)