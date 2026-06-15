from src.vcs.db.sqlite import DBHandler
from src.utils.logger import log_enabled
from src.vcs.adapters.local_adapter import LocalAdapter
from src.vcs.shared.config import BLOB_CONFIG
from src.vcs.services.versioning import deactive_and_reactive_sources

from pathlib import Path
import yaml

class Initializer:
    def __init__(self, db_handler: DBHandler, config_path: Path):
        self.db_handler = db_handler
        self.config_path = Path(config_path)
        self.sources = self._get_sources(config_path)

    @log_enabled
    def process_config(self): 
        file_content = self.config_path.read_bytes()
        #TODO: get event update config -> restart worker (warning)
        (BLOB_CONFIG / "config.blob").write_bytes(file_content)

        #Fetch status with config sources
        deactive_and_reactive_sources(self.db_handler, sources=self.sources)

        for source in self.sources:
            if source["type"] == "local":
                adapter = LocalAdapter(self.db_handler)
                adapter.local_processing(source["path"])

    def _get_sources(self, config_path: Path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config["sources"]
    
    

    
