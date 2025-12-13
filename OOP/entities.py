class User:
    def __init__(self, id: int, username: str, role: str):
        self.id = id
        self.username = username
        self.role = role

    def is_admin(self) -> bool:
        return self.role == "admin"


class Book:
    def __init__(self, id: int, title: str, author: str, year: int, total: int, available: int):
        self.id = id
        self.title = title
        self.author = author
        self.year = year
        self.total = total
        self.available = available


class Loan:
    def __init__(self, id: int, user_id: int, book_id: int, loan_date: str, due_date: str, return_date: str | None):
        self.id = id
        self.user_id = user_id
        self.book_id = book_id
        self.loan_date = loan_date
        self.due_date = due_date
        self.return_date = return_date