from dataclasses import dataclass
from typing import Any, Callable
import sqlite3

@dataclass
class ContextEntry:
    context_id: str
    location: str
    provider: str
    content_hash: str
    
@dataclass
class Locations:
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


