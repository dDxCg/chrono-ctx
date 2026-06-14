from watchdog.events import FileSystemEvent, FileCreatedEvent, FileDeletedEvent, FileModifiedEvent, FileMovedEvent, DirMovedEvent, DirDeletedEvent 
from src.vcs.shared.types import CreatedEvent, DeletedEvent, ModifiedEvent, MovedEvent
from src.utils.helper import path_normalize

def normalize_event(event: FileSystemEvent):
    if not event.src_path:
        return None
    if isinstance(event, FileCreatedEvent):
        return CreatedEvent(src=path_normalize(event.src_path))
    if isinstance(event, FileDeletedEvent):
        return DeletedEvent(src=path_normalize(event.src_path))
    if isinstance(event, FileModifiedEvent):
        return ModifiedEvent(src=path_normalize(event.src_path))
    
    #MoveEvent = rename
    if isinstance(event, FileMovedEvent):
        return MovedEvent(
            src=path_normalize(event.src_path), 
            dst=path_normalize(event.dest_path)
        )
    
    if isinstance(event, DirDeletedEvent):
        return DeletedEvent(src=path_normalize(event.src_path), is_dir=event.is_directory)
    
    #MoveEvent = rename
    if isinstance(event, DirMovedEvent):
        return MovedEvent(
            src=path_normalize(event.src_path),
            dst=path_normalize(event.dest_path),
            is_dir=event.is_directory
        )
    return None
