import os
from dotenv import load_dotenv

def load_db_url():
    load_dotenv()
    MODE = os.getenv("MODE", "dev")
    if MODE == "dev":
        load_dotenv(".env.dev")
        return os.getenv("DATABASE_URL")
    else:
        load_dotenv(".env.prod")
        return os.getenv("DATABASE_URL")
