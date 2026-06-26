from queue import Queue
from src.vcs.shared.types import SourceEvent
from src.utils.logger import log_enabled
from src.vcs.workers.local.utils import STOP


class LocalQueue():
    def __init__(self):
        self.queue = Queue()
        self.closed = False

    @log_enabled
    def publish(self, event):
        if isinstance(event, SourceEvent) or event is STOP:
            self.queue.put(event)
            

    @log_enabled
    def consume(self):
        event = self.queue.get()
        if event is None:
            return None
        return event

    @log_enabled    
    def close(self):
        self.queue.task_done()
         