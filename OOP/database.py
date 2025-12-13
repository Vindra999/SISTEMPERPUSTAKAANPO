import sqlite3
import os

# Menentukan lokasi DB relatif terhadap file ini
DB_PATH = os.path.join(os.path.dirname(__file__), "perpustakaan.db")

class Database:
    def connect(self):
        raise NotImplementedError

class SQLiteDatabase(Database):
    def __init__(self, path: str):
        self.path = path

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn