from collectors.db_handler import DBHandler
from utils.helper import load_db_url

from pathlib import Path
import yaml

class Gateway:
    def __init__(self, db_handler):
        self.db_handler = db_handler

    def get_sources(self, config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config["sources"]

if __name__ == "__main__":
    db_handler = DBHandler(load_db_url())
    gateway = Gateway(db_handler)
    config_path = Path(__file__).parent.parent / "config.yaml"
    sources = gateway.get_sources(config_path)
    print(sources)