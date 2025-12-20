from entities import User, Loan
from utils import PasswordHasher
from ports import UserRepositoryPort, BookRepositoryPort, LoanRepositoryPort
from infrastructure.database import Database


class AuthService:
    def __init__(self, user_repo: UserRepositoryPort, hasher: PasswordHasher):
        self.user_repo = user_repo
        self.hasher = hasher

    def login(self, username: str, password: str):
        row = self.user_repo.find_by_username(username)
        if not row:
            return None
        if self.hasher.verify(row["password_hash"], password):
            return User(row["id"], row["username"], row["role"])
        return None

    def register(self, username: str, password: str):
        self.user_repo.create(username, self.hasher.hash(password), "pengunjung")

    def upsert_admin(self, username: str, password: str):
        self.user_repo.promote_or_upsert_admin(
            username, self.hasher.hash(password)
        )


class BookService:
    def __init__(self, book_repo: BookRepositoryPort):
        self.book_repo = book_repo

    def list_all(self):
        return self.book_repo.list_all()

    def list_available(self):
        return self.book_repo.list_available()

    def search(self, q: str):
        return self.book_repo.search(q)

    def add(self, title, author, year, copies):
        self.book_repo.add(title, author, year, copies)

    def update_stock(self, book_id, total):
        self.book_repo.update_stock(book_id, total)

    def delete(self, book_id):
        self.book_repo.delete(book_id)


class LoanService:
    def __init__(self, loan_repo: LoanRepositoryPort, book_repo: BookRepositoryPort):
        self.loan_repo = loan_repo
        self.book_repo = book_repo

    def borrow(self, user: User, book_id: int):
        # validate business rules first
        book = self.book_repo.get_by_id(book_id)
        if not book:
            raise ValueError("Buku tidak ditemukan")
        if book["copies_available"] <= 0:
            raise ValueError("Buku tidak tersedia")
        if self.loan_repo.find_active_by_user_and_book(user.id, book_id):
            raise ValueError("Anda sudah meminjam buku ini")

        # perform atomic DB operation (decrement + create loan)
        self.loan_repo.create_loan_and_decrease_stock(Loan.create(user.id, book_id))

    def return_book(self, user: User, loan_id: int):
        loan = self.loan_repo.find_active_by_id_and_user(loan_id, user.id)
        if not loan:
            raise ValueError("Data peminjaman tidak ditemukan")

        self.loan_repo.mark_returned(loan_id)
        self.book_repo.increase_stock(loan["book_id"])

    def active_loans_by_user(self, user: User):
        return self.loan_repo.active_loans_by_user(user.id)

    def history_by_user(self, user: User):
        return self.loan_repo.history_by_user(user.id)


class DatabaseInitializer:
    def __init__(self, db: Database, hasher: PasswordHasher, user_repo: UserRepositoryPort):
        self.db = db
        self.hasher = hasher
        self.user_repo = user_repo

    def init(self):
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT,
            created_at TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            year INTEGER,
            copies_total INTEGER,
            copies_available INTEGER,
            created_at TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_id INTEGER,
            loan_date TEXT,
            due_date TEXT,
            return_date TEXT
        )
        """)

        conn.commit()
        conn.close()
