from abc import ABC, abstractmethod
from vcs.db.sqlite import DBHandler

class Consumer(ABC):
    def __init__(self, db_handler):
        self.db_handler = db_handler

    @classmethod
    def from_db_url(cls, db_url):
        db = DBHandler.from_url(db_url)
        return cls(db)

    @abstractmethod
    def handle(self, event):
        pass