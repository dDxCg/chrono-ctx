from pathlib import Path

from utils.helper import get_db_url
from vcs.db.sqlite import DBHandler

def init_db(db_handler: DBHandler):
    import os
    from dotenv import load_dotenv

    db_path = Path(get_db_url())
    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.touch(exist_ok=True)

    load_dotenv()
    SCHEMA_PATH = os.getenv("SCHEMA_PATH", "data/schema.sql")
    db_handler.execute_script(SCHEMA_PATH)

def reset_db(db_handler: DBHandler):
    db_path = Path(get_db_url())
    if db_path.is_file():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.touch(exist_ok=True)
    init_db(db_handler)
    

    

    
    