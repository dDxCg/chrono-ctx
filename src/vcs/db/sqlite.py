import sqlite3
from src.vcs.shared.types import Query

class DBHandler:
    def __init__(self, db_url):
        self.db_url = db_url
        self.conn = None

    def __init__(self, conn):
        self.conn = conn
        self.db_url = None

    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_url)
            
    def execute(self, query: Query, commit: bool = True):
        self.connect()
        cursor = self.conn.cursor()
        if query.params:
            cursor.execute(query.query, query.params)
        else:
            cursor.execute(query.query)
        if commit:
            self.conn.commit()
        return cursor.fetchall()

    def check_connection(self):
        self.execute(commit=False, query=Query(query="SELECT 1"))
        return True

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def commit(self):
        if self.conn:
            self.conn.commit()

    def rollback(self):
        if self.conn:
            self.conn.rollback()

    def begin(self):
        self.execute(commit=False, query=Query(query="BEGIN"))