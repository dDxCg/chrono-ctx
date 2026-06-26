import logging
import threading

from src.vcs.workers.local.local_runtime import LocalWorker
from src.vcs.initialize import Initializer
from src.utils.logger import setup_logger

class VCSRuntime:
    def __init__(self):
        self.stop_event = threading.Event()
        self.init = Initializer()
        self.local_runtime = LocalWorker(self.init.sources, self.stop_event)
        

    def run(self):
        self.init.process_config()

        try:
            self.local_runtime.run()
        except KeyboardInterrupt:
            print("Stopping...")
            self.stop()

    def stop(self):
        self.stop_event.set()
        print(f"RUNTIME - STOP: {self.stop_event}")
        self.local_runtime.stop()


if __name__ == "__main__":
    setup_logger(level=logging.DEBUG)
    vcs_runtime = VCSRuntime()
    vcs_runtime.run()