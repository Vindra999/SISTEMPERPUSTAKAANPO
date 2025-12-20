from datetime import datetime
import sqlite3
from infrastructure.database import Database
from ports import LoanRepositoryPort
from exceptions import UsernameAlreadyExists


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    def find_by_username(self, username: str):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        conn.close()
        return row

    def create(self, username: str, password_hash: str, role: str):
        conn = self.db.connect()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?,?,?,?)",
                (username, password_hash, role, datetime.utcnow().isoformat()),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # map DB integrity error to domain exception
            conn.close()
            raise UsernameAlreadyExists(username)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def promote_or_upsert_admin(self, username: str, password_hash: str):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE users SET role='admin', password_hash=? WHERE id=?",
                (password_hash, row["id"]),
            )
        else:
            self.create(username, password_hash, "admin")
        conn.commit()
        conn.close()

    def list_all(self):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT id, username, role, created_at FROM users ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows


class BookRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_all(self):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM books ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows

    def list_available(self):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM books WHERE copies_available > 0 ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows

    def search(self, q: str):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM books WHERE title LIKE ? OR author LIKE ?",
            (f"%{q}%", f"%{q}%"),
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def add(self, title, author, year, copies):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO books (title, author, year, copies_total, copies_available, created_at) VALUES (?,?,?,?,?,?)",
            (title, author, year, copies, copies, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()

    def get_by_id(self, book_id: int):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM books WHERE id=?", (book_id,))
        row = cur.fetchone()
        conn.close()
        return row

    def decrease_stock(self, book_id: int):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE books SET copies_available = copies_available - 1 WHERE id=?",
            (book_id,),
        )
        conn.commit()
        conn.close()

    def increase_stock(self, book_id: int):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE books SET copies_available = copies_available + 1 WHERE id=?",
            (book_id,),
        )
        conn.commit()
        conn.close()

    def update_stock(self, book_id: int, new_total: int):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT copies_total, copies_available FROM books WHERE id=?", (book_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            raise ValueError("Buku tidak ditemukan")
        current_total = row["copies_total"]
        current_available = row["copies_available"]
        delta = new_total - (current_total or 0)
        new_available = (current_available or 0) + delta
        if new_available < 0:
            new_available = 0
        cur.execute(
            "UPDATE books SET copies_total=?, copies_available=? WHERE id=?",
            (new_total, new_available, book_id),
        )
        conn.commit()
        conn.close()

    def delete(self, book_id: int):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
        conn.close()


class LoanRepository:
    def __init__(self, db: Database):
        self.db = db

    def create(self, data: dict):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO loans (user_id, book_id, loan_date, due_date) VALUES (?,?,?,?)",
            (data["user_id"], data["book_id"], data["loan_date"], data["due_date"]),
        )
        conn.commit()
        conn.close()

    def create_loan_and_decrease_stock(self, data: dict):
        """Atomically decrease book stock and create loan using a single DB transaction."""
        conn = self.db.connect()
        cur = conn.cursor()
        try:
            # check available
            cur.execute("SELECT copies_available FROM books WHERE id=?", (data["book_id"],))
            row = cur.fetchone()
            if not row:
                raise ValueError("Buku tidak ditemukan")
            if row["copies_available"] <= 0:
                raise ValueError("Buku tidak tersedia")

            cur.execute(
                "UPDATE books SET copies_available = copies_available - 1 WHERE id=?",
                (data["book_id"],),
            )
            cur.execute(
                "INSERT INTO loans (user_id, book_id, loan_date, due_date) VALUES (?,?,?,?)",
                (data["user_id"], data["book_id"], data["loan_date"], data["due_date"]),
            )
            conn.commit()
        finally:
            conn.close()

    def find_active_by_user_and_book(self, user_id, book_id):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM loans WHERE user_id=? AND book_id=? AND return_date IS NULL",
            (user_id, book_id),
        )
        row = cur.fetchone()
        conn.close()
        return row is not None

    def find_active_by_id_and_user(self, loan_id, user_id):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM loans WHERE id=? AND user_id=? AND return_date IS NULL",
            (loan_id, user_id),
        )
        row = cur.fetchone()
        conn.close()
        return row

    def mark_returned(self, loan_id: int):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE loans SET return_date=? WHERE id=?",
            (datetime.utcnow().isoformat(), loan_id),
        )
        conn.commit()
        conn.close()

    def active_loans_by_user(self, user_id):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT l.id AS loan_id, b.title, b.author, l.loan_date, l.due_date
            FROM loans l JOIN books b ON b.id = l.book_id
            WHERE l.user_id=? AND l.return_date IS NULL
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def history_by_user(self, user_id):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT b.title, b.author, l.loan_date, l.due_date, l.return_date
            FROM loans l JOIN books b ON b.id = l.book_id
            WHERE l.user_id=?
            ORDER BY l.id DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
        return rows
