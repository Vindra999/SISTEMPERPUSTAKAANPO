from infrastructure.database import SQLiteDatabase, DB_PATH
from infrastructure.repositories import UserRepository, BookRepository, LoanRepository
from application.services import AuthService, BookService, LoanService, DatabaseInitializer
from utils import PasswordHasher
from ui.cli import CLI

if __name__ == "__main__":
    db = SQLiteDatabase(DB_PATH)
    hasher = PasswordHasher()

    user_repo = UserRepository(db)
    book_repo = BookRepository(db)
    loan_repo = LoanRepository(db)

    auth = AuthService(user_repo, hasher)
    books = BookService(book_repo)
    loans = LoanService(loan_repo, book_repo)

    DatabaseInitializer(db, hasher, user_repo).init()

    CLI(auth, books, loans).run()
