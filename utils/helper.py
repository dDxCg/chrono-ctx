import hashlib
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

@log_enabled
def read_file(file_path: str, mode: str = 'rb'):
    file_path = _path_normalize(file_path)
    with open(file_path, mode) as f:
        file_content = f.read()
    return file_content

@log_enabled
def collect_files(path: str) -> list[Path]:
    path = _path_normalize(path)
    p = Path(path).resolve()
    if p.is_file():
        return [p]
    if p.is_dir():
        return [f for f in p.rglob("*") if f.is_file()]

def _path_normalize(path: str) -> str:
    p = Path(path).expanduser()
    p = p.resolve(strict=False)
    return p.as_posix()

def make_dirs(*path: Path):
    for p in path:
        p.mkdir(parents=True, exist_ok=True)

def text_similarity(text_1: str, text_2: str):
    from difflib import SequenceMatcher
    matcher = SequenceMatcher(None, text_1, text_2)

    ratio = matcher.real_quick_ratio()
    if ratio < 0.5:
        return ratio
    
    ratio = matcher.quick_ratio()
    if ratio < 0.8:
        return ratio
    
    return matcher.ratio()

def bytes_to_string(input: bytes):
    return input.decode("utf-8", errors="replace")

def hash(input: str):
    return hashlib.sha256(input).hexdigest()
