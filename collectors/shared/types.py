from dataclasses import dataclass
from typing import Any

@dataclass
class ContextEntry:
    context_id: str
    location: str
    provider: str
    content_hash: str
    
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
    dst: str | None = None