import sqlite3
import os
from dotenv import load_dotenv

class DBHandler:
    def __init__(self, db_url):
        self.db_url = db_url
        self.conn = None

    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_url)

    def execute(self, query, params=None):
        self.connect()
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        self.conn.commit()
        return cursor.fetchall()
    
    def check_connection(self):
        self.execute("SELECT 1")
        print("Connected to database.")

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None