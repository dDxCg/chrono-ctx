
from src.vcs.shared.config import BLOB_ROOT, NEW_VERSION_THRESHOLD
from src.utils.logger import log_enabled
from src.vcs.shared.types import CreatedEvent, ContextEntry, DeletedEvent, MovedEvent, Query, Version, ModifiedEvent
from src.vcs.db.sqlite import DBHandler
from src.utils.helper import text_similarity, bytes_to_string, path_normalize, collect_files
from src.vcs.shared.temp_file import TempFile


@log_enabled
def append_context(db_handler: DBHandler, context_entry: ContextEntry):
    try:
        if _check_existed_version(db_handler, context_entry.content_hash):
            return
        
        context_id = _check_existed_location(db_handler, context_entry.location)

        db_handler.begin()
        
        if context_id is None:
            context_id = context_entry.context_id
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

        version_number = _check_current_version(db_handler, context_id)
        version = Version(version_number = version_number + 1, 
                          context_id = context_id, 
                          content_hash = context_entry.content_hash)
        _append_version(db_handler, version, commit=False)
        db_handler.commit()
    except Exception:
        db_handler.rollback()
        raise 

@log_enabled
def modified_handle(db_handler: DBHandler, event: ModifiedEvent, tmp_file: TempFile) -> bool:
    context_id = _get_context_id_by_location(db_handler, event.src)
    current_version = _check_current_version(db_handler, context_id)
    new_hash = _get_version_hash(db_handler, context_id, current_version)
    if _decide_to_append_version(tmp_file, content_hash=new_hash):
        version = Version(
            version_number=current_version+1,
            context_id=context_id,
            content_hash=new_hash
        )
        _append_version(db_handler, version, commit=True)
        tmp_file.move_tmp_file(BLOB_ROOT / f"{new_hash}.blob")
    else:
        tmp_file.delete_tmp_file()
    

#change old path + add new version via context id
@log_enabled
def moved_handle(db_handler: DBHandler, event: MovedEvent):
    context_id = _get_context_id_by_location(db_handler, event.src)
    update_path = Query(
        query="UPDATE locations SET location = ? WHERE context_id = ?",
        params = (event.dst, context_id)
    )
    db_handler.execute(update_path, commit=True)
    
    
@log_enabled
def created_handle(db_handler: DBHandler, event: CreatedEvent):
    context_entry = ContextEntry.from_path(event.src)
    append_context(db_handler, context_entry)

@log_enabled
def deleted_handle(db_handler: DBHandler, event: DeletedEvent):
    query = Query(
        query = "UPDATE locations SET status = 0 WHERE location = ?",
        params = (event.src,)
    )
    db_handler.execute(commit=True, query=query)

@log_enabled
def deactive_and_reactive_sources(db_handler: DBHandler, sources):
    try:
        db_handler.begin()
        deactive_all = Query(
            query="UPDATE locations SET status = 0"
        ) 
        db_handler.execute(deactive_all, commit=False)
        for source in sources:
            source_path = path_normalize(source["path"])
            file_paths = collect_files(source_path)
            for path in file_paths:
                reactive_query = Query(
                    query = "UPDATE locations SET status = 1 WHERE location = ?",
                    params = (path,)
                )
                db_handler.execute(reactive_query, commit=False)
        db_handler.commit()
    except Exception:
        db_handler.rollback()
        raise
    

def _check_current_version(db_handler: DBHandler, context_id: str):
    get_current_version = Query(
        query = "SELECT COALESCE(MAX(version_number), 0) FROM versions WHERE context_id = ?",
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

def _get_context_id_by_location(db_handler: DBHandler, location: str):
    get_context_id = Query(
        query = "SELECT context_id FROM locations WHERE location = ?",
        params = (location,)
    )
    res = db_handler.execute(commit=False, query=get_context_id)
    return res[0][0]

    
def _decide_to_append_version(tmp_file: TempFile, content_hash: str) -> bool:
    upcoming_blob = tmp_file.read_bytes()
    current_blob = (BLOB_ROOT / f"{content_hash}.blob").read_bytes()
    similarity = text_similarity(bytes_to_string(current_blob), bytes_to_string(upcoming_blob))
    if similarity < NEW_VERSION_THRESHOLD:
        return True
    return False

def _get_version_hash(db_handler: DBHandler, context_id: str, version_number: int):
    get_content_hash = Query(
        query = "SELECT content_hash from versions WHERE context_id = ? AND version_number = ?",
        params = (context_id, version_number)
    )
    res = db_handler.execute(commit=False, query=get_content_hash)
    return res[0][0]


def _check_existed_version(db_handler: DBHandler, content_hash: str) -> bool:
    check_content_hash = Query(
        query = """SELECT c.context_id 
                FROM contexts c JOIN versions v ON c.context_id = v.context_id 
                WHERE v.content_hash = ?""",
        params = (content_hash,)
    )
    result = db_handler.execute(commit=False, query=check_content_hash)
    return bool(result)

def _check_existed_location(db_handler: DBHandler, location: str):
    check_path = Query(
        query="SELECT context_id FROM locations WHERE location = ?",
        params = (location,)
    )
    res = db_handler.execute(commit=False, query = check_path)
    if res:
        return res[0][0]
    return None
    