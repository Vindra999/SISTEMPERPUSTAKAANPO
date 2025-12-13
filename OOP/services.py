import sqlite3
from datetime import datetime
from database import Database, SQLiteDatabase, DB_PATH
from repositories import UserRepository, BookRepository, LoanRepository
from entities import User
from utils import PasswordHasher

class AuthService:
    def __init__(self, user_repo: UserRepository, hasher: PasswordHasher):
        self.user_repo = user_repo
        self.hasher = hasher

    def login(self, username: str, password: str) -> User | None:
        row = self.user_repo.find_by_username(username)
        if not row:
            return None
        if self.hasher.verify(row["password_hash"], password):
            return User(row["id"], row["username"], row["role"])
        return None

    def register(self, username: str, password: str):
        self.user_repo.create(username, self.hasher.hash(password), "pengunjung")

    def upsert_admin(self, username: str, password: str):
        self.user_repo.promote_or_upsert_admin(username, self.hasher.hash(password))


class BookService:
    def __init__(self, book_repo: BookRepository):
        self.book_repo = book_repo

    def list_all(self):
        return self.book_repo.list_all()

    def list_available(self):
        return self.book_repo.list_available()

    def search(self, q: str):
        return self.book_repo.search(q)

    def add(self, title: str, author: str, year: int | None, copies: int):
        self.book_repo.add(title, author, year, copies)

    def update_stock(self, book_id: int, new_total: int):
        self.book_repo.update_stock(book_id, new_total)

    def delete(self, book_id: int):
        self.book_repo.delete(book_id)


class LoanService:
    def __init__(self, loan_repo: LoanRepository, book_repo: BookRepository):
        self.loan_repo = loan_repo
        self.book_repo = book_repo

    def borrow(self, user: User, book_id: int):
        book = self.book_repo.get_by_id(book_id)
        if not book:
            raise ValueError("Buku tidak ditemukan")
        if book["copies_available"] <= 0:
            raise ValueError("Buku sedang tidak tersedia")
        if self.loan_repo.is_already_borrowed(user.id, book_id):
            raise ValueError("Anda sudah meminjam buku ini dan belum mengembalikannya")
        self.loan_repo.borrow(user.id, book_id)

    def return_book(self, user: User, loan_id: int):
        # Kita perlu koneksi sementara untuk cek kepemilikan loan
        # Idealnya LoanRepository punya method find_by_id_and_user, 
        # tapi kita pakai logic asli untuk konsistensi.
        conn = SQLiteDatabase(DB_PATH).connect()
        cur = conn.cursor()
        cur.execute("SELECT book_id FROM loans WHERE id=? AND user_id=? AND return_date IS NULL", (loan_id, user.id))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            raise ValueError("Data peminjaman tidak ditemukan")
        self.loan_repo.return_book(loan_id, row["book_id"])

    def active_loans_by_user(self, user: User):
        return self.loan_repo.active_loans_by_user(user.id)

    def history_by_user(self, user: User):
        return self.loan_repo.history_by_user(user.id)


class DatabaseInitializer:
    def __init__(self, db: Database, hasher: PasswordHasher, user_repo: UserRepository):
        self.db = db
        self.hasher = hasher
        self.user_repo = user_repo

    def init(self):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','pengunjung')),
                created_at TEXT NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER,
                copies_total INTEGER NOT NULL DEFAULT 1,
                copies_available INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                loan_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()

        # ensure default admin or promote existing 'admin'
        cur.execute("SELECT id FROM users WHERE role='admin' LIMIT 1;")
        has_admin = cur.fetchone()
        if not has_admin:
            # try promote 'admin'
            cur.execute("SELECT id FROM users WHERE username='admin' LIMIT 1;")
            ex = cur.fetchone()
            if ex:
                cur.execute("UPDATE users SET role='admin' WHERE id=?", (ex["id"],))
            else:
                self.user_repo.create("admin", self.hasher.hash("admin123"), "admin")
            conn.commit()
        conn.close()