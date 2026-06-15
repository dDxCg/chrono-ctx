import logging

from src.vcs.workers.local.local_runtime import LocalRuntime
from src.vcs.initialize import Initializer
from src.utils.helper import get_config_path, get_db_url
from src.utils.logger import setup_logger
from src.vcs.db.sqlite import DBHandler

class VCSRuntime:
    def __init__(self, db_handler: DBHandler):
        self.init = Initializer(db_handler, get_config_path())
        self.local_runtime = LocalRuntime(db_handler, self.init.sources)

    def run(self):
        self.init.process_config()
        try:
            self.local_runtime.run()
        except KeyboardInterrupt:
            self.local_runtime.stop()


if __name__ == "__main__":
    setup_logger(level=logging.DEBUG)
    vcs_runtime = VCSRuntime(db_handler=DBHandler.from_url(get_db_url()))
    vcs_runtime.run()