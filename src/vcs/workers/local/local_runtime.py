from src.vcs.workers.local.local_watcher import WatchWorker
from src.vcs.workers.local.local_queue import LocalQueue
from src.vcs.workers.local.local_consumer import LocalConsumer, ConsumerWorker
from src.vcs.db.sqlite import DBHandler

STOP = object()

class LocalRuntime:
    def __init__(self, db_handler: DBHandler, sources):
        self.watcher = WatchWorker()
        self.queue = LocalQueue()
        self.consumer = LocalConsumer(db_handler)
        self.consumer_worker = ConsumerWorker(
            self.queue,
            self.consumer
        )
        self._init_worker(sources)

    def _init_worker(self, sources):
        for source in sources:
            if source["type"] == "local":
                self.watcher.add_watch(
                    source["path"], 
                    callback=self.queue.publish
                )

    def run(self):
        self.consumer_worker.start()
        self.watcher.start()
        try:
            self.consumer_worker.join()

        except KeyboardInterrupt:
            self.stop()
            
    def stop(self):
        self.watcher.stop()
        self.queue.publish(STOP)
        self.consumer_worker.join()