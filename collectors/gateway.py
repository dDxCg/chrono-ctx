import hashlib
from datetime import datetime

from app.db_handler import DBHandler
from utils.helper import load_db_url, save_to_file, read_file
from utils.logger import log_enabled
from collectors.adapters.local_adapter import LocalAdapter
from collectors.shared.config import BLOB_CONFIG

from pathlib import Path
import yaml

class Gateway:
    def __init__(self, db_handler: DBHandler):
        self.db_handler = db_handler

    @log_enabled("Process configuration file")
    def process_config(self, config_path): 
        file_content = read_file(config_path, 'rb')
        
        save_to_file(file_content, BLOB_CONFIG / f"config.blob", mode="wb")

        sources = self._get_sources(config_path)
        for source in sources:
            if source["type"] == "local":
                adapter = LocalAdapter(self.db_handler)
                adapter.local_processing(source["path"])

    def _get_sources(self, config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config["sources"]
    
    def analyze_events(self):
        pass

    
if __name__ == "__main__":
    from utils.logger import setup_logger
    setup_logger()
    db_handler = DBHandler(load_db_url())
    gateway = Gateway(db_handler)
    config_path = Path(__file__).parent.parent / "config.yaml"
    gateway.process_config(config_path)