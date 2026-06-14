from src.vcs.db.sqlite import DBHandler
from src.utils.helper import load_db_url
from src.utils.logger import log_enabled
from src.vcs.adapters.local_adapter import LocalAdapter
from src.vcs.shared.config import BLOB_CONFIG
from src.vcs.services.versioning import deactive_and_reactive_sources

from pathlib import Path
import yaml

class Gateway:
    def __init__(self, db_handler: DBHandler):
        self.db_handler = db_handler

    @log_enabled
    def process_config(self, config_path: Path): 
        file_content = config_path.read_bytes()
        #TODO: get event update config -> restart worker (warning)
        (BLOB_CONFIG / "config.blob").write_bytes(file_content)

        sources = self._get_sources(config_path)

        #Fetch status with config sources
        deactive_and_reactive_sources(self.db_handler, sources=sources)

        for source in sources:
            if source["type"] == "local":
                adapter = LocalAdapter(self.db_handler)
                adapter.local_processing(source["path"])

    def _get_sources(self, config_path: Path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config["sources"]
    
    def analyze_events(self):
        pass

    
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    import logging
    setup_logger(logging.DEBUG)
    db_path = load_db_url()
    db_handler = DBHandler(db_url=db_path)
    gateway = Gateway(db_handler)
    config_path = Path("config.yaml")
    gateway.process_config(config_path)