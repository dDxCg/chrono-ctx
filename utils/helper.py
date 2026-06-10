import os
from dotenv import load_dotenv
from pathlib import Path
from utils.logger import log_enabled

@log_enabled("Load mode and database URL")
def load_db_url():
    load_dotenv()
    MODE = os.getenv("MODE", "dev")
    if MODE == "dev":
        load_dotenv(".env.dev")
        return os.getenv("DATABASE_URL")
    else:
        load_dotenv(".env.prod")
        return os.getenv("DATABASE_URL")
    
@log_enabled("Save data to file")
def save_to_file(data, file_path, mode="wb"):
    with open(file_path, mode) as f:
        f.write(data)

def make_dirs(*path: Path):
    for p in path:
        p.mkdir(parents=True, exist_ok=True)

def path_normalize(path: str) -> str:
    p = Path(path).expanduser()
    p = p.resolve(strict=False)
    return p.as_posix()

def collect_files(path: str) -> list[Path]:
    p = Path(path).resolve()

    if p.is_file():
        return [p]

    if p.is_dir():
        return [f for f in p.rglob("*") if f.is_file()]

def content_similarity(content1: str, content2: str) -> float:
    set1 = set(content1.split())
    set2 = set(content2.split())
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    if not union:
        return 0.0
    return len(intersection) / len(union)