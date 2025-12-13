import sqlite3
from datetime import datetime
from database import Database

class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    def find_by_username(self, username: str) -> sqlite3.Row | None:
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        conn.close()
        return row

    def create(self, username: str, password_hash: str, role: str):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?,?,?,?)",
            (username, password_hash, role, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()

    def promote_or_upsert_admin(self, username: str, password_hash: str):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE users SET role='admin', password_hash=? WHERE id=?", (password_hash, row["id"]))
        else:
            cur.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?,?,?,?)",
                (username, password_hash, "admin", datetime.utcnow().isoformat()),
            )
        conn.commit()
        conn.close()

    def list_all(self) -> list[sqlite3.Row]:
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT id, username, role, created_at FROM users ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows


class BookRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_all(self) -> list[sqlite3.Row]:
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM books ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows

    def list_available(self) -> list[sqlite3.Row]:
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM books WHERE copies_available > 0 ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows

    def search(self, q: str) -> list[sqlite3.Row]:
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? ORDER BY id",
            (f"%{q}%", f"%{q}%"),
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def add(self, title: str, author: str, year: int | None, copies: int):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO books (title, author, year, copies_total, copies_available, created_at) VALUES (?,?,?,?,?,?)",
            (title, author, year, copies, copies, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()

    def get_by_id(self, book_id: int) -> sqlite3.Row | None:
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM books WHERE id=?", (book_id,))
        row = cur.fetchone()
        conn.close()
        return row

    def update_stock(self, book_id: int, new_total: int):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT copies_total, copies_available FROM books WHERE id=?", (book_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            raise ValueError("Buku tidak ditemukan")
        old_total = row["copies_total"]
        old_available = row["copies_available"]
        diff = new_total - old_total
        new_available = old_available + diff
        if new_available < 0:
            conn.close()
            raise ValueError("Tidak bisa mengurangi total di bawah jumlah yang sedang dipinjam")
        cur.execute("UPDATE books SET copies_total=?, copies_available=? WHERE id=?", (new_total, new_available, book_id))
        conn.commit()
        conn.close()

    def delete(self, book_id: int):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM loans WHERE book_id=? AND return_date IS NULL", (book_id,))
        if cur.fetchone()[0] > 0:
            conn.close()
            raise ValueError("Tidak bisa menghapus: masih ada peminjaman aktif untuk buku ini")
        cur.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
        conn.close()


class LoanRepository:
    def __init__(self, db: Database):
        self.db = db

    def active_loans_by_user(self, user_id: int) -> list[sqlite3.Row]:
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT l.id as loan_id, b.id as book_id, b.title, b.author, l.loan_date, l.due_date
            FROM loans l JOIN books b ON b.id = l.book_id
            WHERE l.user_id=? AND l.return_date IS NULL
            ORDER BY l.id
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def history_by_user(self, user_id: int) -> list[sqlite3.Row]:
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

    def is_already_borrowed(self, user_id: int, book_id: int) -> bool:
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(1) FROM loans WHERE user_id=? AND book_id=? AND return_date IS NULL",
            (user_id, book_id),
        )
        already = cur.fetchone()[0]
        conn.close()
        return already > 0

    def borrow(self, user_id: int, book_id: int):
        # Perhatikan: Repository ini menangani database langsung. 
        # Logic timedelta dipindah ke sini atau disiapkan di Service. 
        # Di kode asli, logic ada di sini.
        from datetime import datetime, timedelta # local import
        conn = self.db.connect()
        cur = conn.cursor()
        now = datetime.utcnow()
        due = now + timedelta(days=7)
        cur.execute(
            "INSERT INTO loans (user_id, book_id, loan_date, due_date) VALUES (?,?,?,?)",
            (user_id, book_id, now.isoformat(), due.isoformat()),
        )
        cur.execute("UPDATE books SET copies_available = copies_available - 1 WHERE id=?", (book_id,))
        conn.commit()
        conn.close()

    def return_book(self, loan_id: int, book_id: int):
        conn = self.db.connect()
        cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        cur.execute("UPDATE loans SET return_date=? WHERE id=?", (now, loan_id))
        cur.execute("UPDATE books SET copies_available = copies_available + 1 WHERE id=?", (book_id,))
        conn.commit()
        conn.close()