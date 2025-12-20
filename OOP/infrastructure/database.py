import sqlite3

DB_PATH = "perpustakaan.db"


class Database:
    def connect(self):
        raise NotImplementedError


class SQLiteDatabase(Database):
    def __init__(self, path: str):
        self.path = path

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn
