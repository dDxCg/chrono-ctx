from queue import Queue
from vcs.shared.types import SourceEvent
from utils.logger import log_enabled
from vcs.workers.utils import STOP
from vcs.workers.interfaces.event_broker import EventBroker


class LocalQueue(EventBroker):
    def __init__(self):
        super().__init__()
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
         