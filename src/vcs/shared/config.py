from pathlib import Path
from src.utils.helper import make_dirs

BLOB_ROOT = Path("data/blobs")
BLOB_CONFIG = BLOB_ROOT / "configs"

make_dirs(
    BLOB_ROOT, 
    BLOB_CONFIG
)

NEW_VERSION_THRESHOLD = 0.9