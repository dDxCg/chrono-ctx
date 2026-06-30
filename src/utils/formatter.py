from watchdog.events import FileSystemEvent, FileCreatedEvent, FileDeletedEvent, FileModifiedEvent, FileMovedEvent, DirMovedEvent, DirDeletedEvent
from vcs.shared.types import CreatedEvent, DeletedEvent, ModifiedEvent, MovedEvent, ConfigCreatedEvent, ConfigDeletedEvent, ConfigModifiedEvent, ConfigMovedEvent
from utils.helper import path_normalize, get_config_path

def normalize_event(event: FileSystemEvent):
    if not event.src_path:
        return None
    src = path_normalize(event.src_path)
    config_path = path_normalize(get_config_path())
    if isinstance(event, FileCreatedEvent):
        if src == config_path:
            return ConfigCreatedEvent()
        return CreatedEvent(src)
    if isinstance(event, FileDeletedEvent):
        if src == config_path:
            return ConfigDeletedEvent()
        return DeletedEvent(src)
    if isinstance(event, FileModifiedEvent):
        if src == config_path:
            return ConfigModifiedEvent()
        return ModifiedEvent(src)
    
    #MoveEvent = rename
    if isinstance(event, FileMovedEvent):
        if src == config_path:
            return ConfigMovedEvent(
                src,
                dst = path_normalize(event.dest_path) 
            )
        return MovedEvent(
            src=src, 
            dst=path_normalize(event.dest_path)
        )
    
    if isinstance(event, DirDeletedEvent):
        return DeletedEvent(src=src, is_dir=event.is_directory)
    
    #MoveEvent = rename
    if isinstance(event, DirMovedEvent):
        return MovedEvent(
            src=src,
            dst=path_normalize(event.dest_path),
            is_dir=event.is_directory
        )
    return None
