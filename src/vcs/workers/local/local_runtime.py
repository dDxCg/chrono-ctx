from vcs.workers.local.local_watcher import WatchWorker
from vcs.workers.local.local_consumer import LocalConsumerWorker
from vcs.workers.local.utils import STOP

class LocalWorker:
    def __init__(self, sources, stop_event):
        self.watcher = WatchWorker(stop_event)
        self.stop_event = stop_event
        self.consumer_worker = LocalConsumerWorker(self.stop_event)
        self._init_worker(sources)

    def _init_worker(self, sources):
        for source in sources:
            if source["type"] == "local":
                self.watcher.add_watch(
                    source["path"], 
                    callback=self.consumer_worker.queue.publish
                )

    def run(self):
        self.watcher.start()
        self.consumer_worker.start()
        # print(f"[LOCAL RUNTIME - STOP]: {self.stop_event}")
        try:
            while not self.stop_event.is_set():
                self.stop_event.wait(timeout=1.0)
        except KeyboardInterrupt:
            self.stop()
            
  
    def stop(self):
        self.stop_event.set()
        self.watcher.stop()
        self.consumer_worker.queue.publish(STOP)
        self.consumer_worker.join()