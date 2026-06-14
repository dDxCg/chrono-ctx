from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import uuid

@dataclass
class ContextEntry:
    context_id: str
    location: str
    provider: str
    content_hash: str

    #Construct for local path
    def __init__(self, path: Path):
        file_content = path.read_bytes()
        self.content_hash = hash(file_content)
        self.context_id = str(uuid.uuid4())
        self.location = path
        self.provider = 'local'

    def __init__(self, context_id: str, location: str, provider: str, content_hash: str):
        self.context_id = context_id
        self.location = location
        self.provider = provider
        self.content_hash = content_hash


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
    provider: str
    src: str
    action: str

@dataclass
class AddEvent(SourceEvent):
    action: str = field(init=False, default="added")

@dataclass
class ModifyEvent(SourceEvent):
    action: str = field(init=False, default="modified")

@dataclass
class DeleteEvent(SourceEvent):
    action: str = field(init=False, default="deleted")

@dataclass
class MoveEvent(SourceEvent):
    action: str = field(init=False, default="moved")
    dst: str

