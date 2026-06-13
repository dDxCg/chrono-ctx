from src.vcs.shared.config import BLOB_ROOT, NEW_VERSION_THRESHOLD
from src.utils.logger import log_enabled
from src.vcs.shared.types import ContextEntry, Location, Query, Version
from src.vcs.db_handler import DBHandler
from src.utils.helper import read_file, text_similarity, bytes_to_string, hash

@log_enabled("Add context to database")
def append_context(db_handler: DBHandler, context_entry: ContextEntry):
    try:
        if check_context_exists(db_handler, context_entry.content_hash):
            return

        db_handler.begin()
        add_context = Query(
            query = "INSERT INTO contexts (context_id) VALUES (?)",
            params = (context_entry.context_id,)
        )
        add_location = Query(
            query = "INSERT INTO locations (context_id, location, provider) VALUES (?, ?, ?)",
            params = (context_entry.context_id, context_entry.location, context_entry.provider)
        )
        db_handler.execute(commit=False, query=add_context)
        db_handler.execute(commit=False, query=add_location)

        version_number = _check_current_version(db_handler, context_entry.context_id)
        version = Version(version_number = version_number, 
                          context_id = context_entry.context_id, 
                          content_hash = context_entry.content_hash)
        _append_version(db_handler, version, commit=False)
        db_handler.commit()
    except Exception:
        db_handler.rollback()
        raise 

def check_context_exists(db_handler: DBHandler, content_hash: str) -> bool:
    check_content_hash = Query(
        query = """SELECT c.context_id 
                FROM contexts c JOIN versions v ON c.context_id = v.context_id 
                WHERE v.content_hash = ?""",
        params = (content_hash,)
    )
    result = db_handler.execute(commit=False, query=check_content_hash)
    return bool(result)

#issue: same path + diff context_id
#to do: tmp file handler: create, GC
@log_enabled
def content_modify_handle(db_handler: DBHandler, location: Location, tmp_blob_path: str, commit: bool) -> bool:
    get_context_id = Query(
        query = "SELECT context_id FROM locations WHERE location = ?",
        params = (location.location,)
    )
    res = db_handler.execute(commit=False, query=get_context_id)
    context_id = res[0][0]
    current_version = _check_current_version(context_id)
    get_content_hash = Query(
        query = "SELECT content_hash from versions WHERE context_id = ? AND version_number = ?",
        params = (context_id, current_version)
    )
    res = db_handler.execute(commit=False, query=get_content_hash)
    content_hash = res[0][0]
    latest_blob = read_file(BLOB_ROOT / f"{content_hash}.blob", mode="rb")
    current_blob = read_file(tmp_blob_path, mode="rb")
    similarity = text_similarity(bytes_to_string(latest_blob), bytes_to_string(current_blob))
    if similarity < NEW_VERSION_THRESHOLD:
        version = Version(
            version_number=current_version+1,
            context_id=context_id,
            content_hash=hash(current_blob)
        )
        _append_version(db_handler, version, commit)
        return True
    return False
    

#change location events: similarity deleted file blob and added file blob -> new context/new version + update locations

def _check_current_version(db_handler: DBHandler, context_id: str):
    get_current_version = Query(
        query = "SELECT MAX(version_number) FROM versions WHERE context_id = ?",
        params = (context_id,)
    )
    result = db_handler.execute(commit=False, query=get_current_version)
    return result[0][0] 

def _append_version(db_handler: DBHandler, version: Version, commit: bool):
    create_version = Query(
            query = "INSERT INTO versions (version_number, context_id, content_hash) VALUES (?, ?, ?)",
            params = (version.version_number, version.context_id, version.content_hash)
        )
    db_handler.execute(commit=commit, query=create_version)


