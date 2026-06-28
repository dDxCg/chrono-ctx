import sqlite3
from vcs.shared.types import Query

class DBHandler:
    def __init__(self, conn=None):
        self.conn = conn

    @classmethod
    def from_url(cls, db_url):
        conn = sqlite3.connect(db_url)
        return cls(conn)
            
    def execute(self, query: Query, commit: bool = True):
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