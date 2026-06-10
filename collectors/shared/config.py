from pathlib import Path
from utils.helper import make_dirs

BLOB_ROOT = Path("data/blobs")
BLOB_CONFIG = BLOB_ROOT / "configs"

make_dirs(
    BLOB_ROOT, 
    BLOB_CONFIG
)
