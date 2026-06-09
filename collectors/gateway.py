from pdb import main

from collectors.db_handler import DBHandler
from utils.helper import load_db_url

if __name__ == "__main__":
    db_handler = DBHandler(load_db_url())
    db_handler.check_connection()