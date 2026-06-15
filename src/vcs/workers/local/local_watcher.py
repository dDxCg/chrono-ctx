import time
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.utils.formatter import normalize_event
from src.vcs.shared.types import SourceEvent
from src.utils.logger import setup_logger


class WatchWorker:
    def __init__(self, debounce=0.5):
        self.observer = Observer()
        self.jobs = []
        self.debounce = debounce
        self.last_event = {}

    def _should_process(self, path):
        now = time.time()
        last = self.last_event.get(path, 0)

        if now - last < self.debounce:
            return False

        self.last_event[path] = now
        return True

    def add_watch(self, path, callback, recursive=True):
        worker = self

        class Handler(FileSystemEventHandler):
            def on_any_event(self, event):
                normalized = normalize_event(event)
                if normalized is None:
                    return

                if not worker._should_process(normalized.src):
                    return

                try:
                    logging.info(f"[WATCH] {normalized.src}")
                    callback(normalized)

                except Exception as e:
                    logging.error(f"[WATCH ERROR] {e}")

        self.observer.schedule(Handler(), path, recursive=recursive)
        self.jobs.append((path, callback))

    def start(self):
        logging.info("WatchWorker starting...")
        self.observer.start()

    def stop(self):
        logging.info("WatchWorker stopping...")
        self.observer.stop()
        self.observer.join()

    def run(self):
        try:
            self.start()
            while True:
                self.observer.join(1)
        except KeyboardInterrupt:
            self.stop()


# if __name__ == "__main__":
#     setup_logger(level=logging.INFO)
#     watch_worker = WatchWorker()
#     src_path = "knowledge.example"
    
#     def sample_callback(event: SourceEvent):
#         print(event)

#     watch_worker.add_watch(path=src_path, callback=sample_callback)
#     watch_worker.run()