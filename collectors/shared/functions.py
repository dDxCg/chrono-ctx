from utils.logger import log_enabled
from collectors.shared.types import ContextEntry, Query
from collectors.db_handler import DBHandler

@log_enabled("Add context to database")
def append_context(db_handler: DBHandler, context_entry: ContextEntry):
    try:
        db_handler.begin()
        context_id = _get_or_create_context(db_handler, context_entry)

        get_version = Query(
            query = """
                SELECT COALESCE(MAX(version_number), 0) + 1 
                FROM versions WHERE context_id = %s
            """,
            params = (context_id,)
        )
        result = db_handler.execute(commit=False, query=get_version)
        version_number = result[0][0]

        create_version = Query(
            query = "INSERT INTO versions (version_number, context_id, content_hash) VALUES (%s, %s, %s)",
            params = (version_number, context_id, context_entry.content_hash)
        )
        db_handler.execute(commit=False, query=create_version)
        db_handler.commit()
    except Exception:
        db_handler.rollback()
        raise 

@log_enabled("Get or create context in database")
def _get_or_create_context(db_handler: DBHandler, context_entry: ContextEntry):
    check_content_hash = Query(
        query = """SELECT context_id 
                FROM contexts c JOIN versions v ON c.context_id = v.context_id 
                WHERE v.content_hash = %s""",
        params = (context_entry.content_hash,)
    )
    result = db_handler.execute(commit=False, query=check_content_hash)
    if result:
        return result[0][0]
    else:
        add_context = Query(
            query = "INSERT INTO contexts (context_id) VALUES (%s)",
            params = (context_entry.context_id,)
        )
        add_location = Query(
            query = "INSERT INTO locations (context_id, location, provider) VALUES (%s, %s, %s)",
            params = (context_entry.context_id, context_entry.location, context_entry.provider)
        )
        db_handler.execute(commit=False, query=add_context)
        db_handler.execute(commit=False, query=add_location)
        return context_entry.context_id