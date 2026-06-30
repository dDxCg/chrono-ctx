import threading
from typing import Type

from utils.helper import get_db_url
from vcs.workers.interfaces.consumer import Consumer
from vcs.workers.interfaces.event_broker import EventBroker
from vcs.workers.local.local_consumer import LocalConsumer
from vcs.workers.local.local_queue import LocalQueue
from vcs.workers.utils import STOP


class ConsumerWorker(threading.Thread):
    def __init__(
            self, 
            stop_event, 
            consumer_cls: Type[Consumer] = LocalConsumer, 
            event_broker_cls: Type[EventBroker] = LocalQueue, 
            queue=None
        ):
            super().__init__()
            if queue:
                self.queue = queue
            else:
                self.queue = event_broker_cls()
            self.stop_event = stop_event
            self.consumer_cls = consumer_cls

    def run(self):
        self.consumer = self.consumer_cls.from_db_url(get_db_url())
        while True:
            event = self.queue.consume()

            if event is STOP:
                self.queue.close()
                break

            self.consumer.handle(event)