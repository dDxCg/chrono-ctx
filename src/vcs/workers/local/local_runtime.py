from vcs.workers.local.local_consumer import LocalConsumer
from vcs.workers.local.local_queue import LocalQueue
from vcs.workers.local.local_watcher import WatchWorker
from vcs.workers.consumer_worker import ConsumerWorker
from vcs.workers.config.config_consumer import ConfigConsumer, ConfigConsumerWorker
from vcs.workers.utils import STOP

class LocalRuntime:
    def __init__(self, sources, stop_event, watcher=None, queue=None):
        self.stop_event = stop_event
        
        if watcher:
            self.watcher = watcher
        else:
            self.watcher = WatchWorker(self.stop_event)
        
        self.consumer_worker = ConsumerWorker(
            self.stop_event, 
            queue=queue 
        )

        if queue:
            self.queue = queue
        else:
            self.queue = self.consumer_worker.queue

        self.config_consumer_worker = ConfigConsumerWorker(
            self.stop_event,
            queue=self.queue,
            runtime=self
        )
        
        
        
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
        self.config_consumer_worker.start()
        
        try:
            while not self.stop_event.is_set():
                self.stop_event.wait(timeout=1.0)
        except KeyboardInterrupt:
            self.stop()
            
  
    def stop(self):
        self.stop_event.set()
        self.watcher.stop()
        self.queue.publish(STOP)
        self.consumer_worker.join()
        self.config_consumer_worker.join()