from queue import Empty, Queue
from src.vcs.shared.types import SourceEvent
from src.utils.logger import log_enabled

class LocalQueue(Queue):
    def __init__(self):
        self.queue = Queue()

    @log_enabled
    def publish(self, event):
        if isinstance(event, SourceEvent):
            self.queue.put(event)

    @log_enabled
    def consume(self):
        try:
            return self.queue.get()
        except Empty:
            return None