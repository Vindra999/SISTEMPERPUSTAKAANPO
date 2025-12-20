# Sistem Perpustakaan - Struktur Proyek


## 📁 Struktur Folder

```
OOP/
├── main.py                    # Entry point aplikasi
├── entities.py                # Domain entities (User, Book, Loan)
├── exceptions.py              # Domain-specific exceptions
├── ports.py                   # Protocol/abstraksi untuk DIP (Dependency Inversion)
├── utils.py                   # Utility functions (hashing, UI helpers)
│
├── infrastructure/            # Infrastructure layer (DB, repository implementation)
│   ├── __init__.py
│   ├── database.py            # Database abstraction & SQLite implementation
│   └── repositories.py        # UserRepository, BookRepository, LoanRepository
│
├── application/               # Application layer (business logic & services)
│   ├── __init__.py
│   └── services.py            # AuthService, BookService, LoanService, DatabaseInitializer
│
└── ui/                        # User Interface layer (CLI)
    ├── __init__.py
    └── cli.py                 # Command-line interface
```

## 📝 File-File Penting

| File | Tujuan |
|------|--------|
| `main.py` | Bootstrap aplikasi, setup DI |
| `entities.py` | Domain models (User, Book, Loan) |
| `exceptions.py` | Domain exceptions |
| `ports.py` | Protocol/interface untuk DIP |
| `utils.py` | Helper: PasswordHasher, clear_screen, pause |
| `infrastructure/database.py` | SQLite DB abstraction |
| `infrastructure/repositories.py` | Data access layer |
| `application/services.py` | Business logic & use cases |
| `ui/cli.py` | Command-line interface |
