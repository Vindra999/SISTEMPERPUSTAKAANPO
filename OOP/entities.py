from datetime import datetime, timedelta


class User:
    def __init__(self, id: int, username: str, role: str):
        self.id = id
        self.username = username
        self.role = role

    def is_admin(self) -> bool:
        return self.role == "admin"


class Book:
    def __init__(self, id, title, author, year, total, available):
        self.id = id
        self.title = title
        self.author = author
        self.year = year
        self.total = total
        self.available = available

    def can_be_borrowed(self) -> bool:
        return self.available > 0


class Loan:
    LOAN_DAYS = 7

    @staticmethod
    def create(user_id: int, book_id: int) -> dict:
        now = datetime.utcnow()
        return {
            "user_id": user_id,
            "book_id": book_id,
            "loan_date": now.isoformat(),
            "due_date": (now + timedelta(days=Loan.LOAN_DAYS)).isoformat(),
        }
