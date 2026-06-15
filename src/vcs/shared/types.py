from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from src.utils.helper import gen_ulid

@dataclass
class ContextEntry:
    context_id: str
    location: str
    provider: str
    content_hash: str

    #Construct for local path
    def __init__(
            self, 
            context_id: str, 
            location: str, 
            provider: str, 
            content_hash: str 
            ):
            self.context_id = context_id
            self.location = location
            self.provider = provider
            self.content_hash = content_hash

    @classmethod
    def from_path(cls, path: Path):
        file_content = Path(path).read_bytes()
        content_hash = hash(file_content)
        context_id = gen_ulid()
        location = path
        provider = 'local'
        return cls(context_id, location, provider, content_hash)
        
@dataclass
class Location:
    context_id: str
    location: str
    provider: str
    status: int

@dataclass
class Version:
    version_number: int 
    context_id: str
    content_hash: str

@dataclass
class Query:
    query: str
    params: tuple[Any, ...] | None = None

@dataclass
class SourceEvent:
    src: str
    type: str
    provider: str = "local"
    is_dir: bool = False

@dataclass
class CreatedEvent(SourceEvent):
    type: str = field(init=False, default="added")

@dataclass
class ModifiedEvent(SourceEvent):
    type: str = field(init=False, default="modified")

@dataclass
class DeletedEvent(SourceEvent):
    type: str = field(init=False, default="deleted")

@dataclass(kw_only=True)
class MovedEvent(SourceEvent):
    type: str = field(init=False, default="moved")
    dst: str

