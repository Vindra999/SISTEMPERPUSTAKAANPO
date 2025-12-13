import sys
from database import SQLiteDatabase, DB_PATH
from utils import PasswordHasher, clear_screen
from repositories import UserRepository, BookRepository, LoanRepository
from services import AuthService, BookService, LoanService, DatabaseInitializer
from cli import CLI

if __name__ == "__main__":
    try:
        # Inisialisasi arsitektur SOLID
        db = SQLiteDatabase(DB_PATH)
        hasher = PasswordHasher()
        user_repo = UserRepository(db)
        book_repo = BookRepository(db)
        loan_repo = LoanRepository(db)
        
        auth = AuthService(user_repo, hasher)
        books = BookService(book_repo)
        loans = LoanService(loan_repo, book_repo)
        
        # Inisialisasi Database (Table creation & Default Admin)
        initializer = DatabaseInitializer(db, hasher, user_repo)
        initializer.init()

        # Mode diagnostik opsional
        if "--list-users" in sys.argv:
            rows = user_repo.list_all()
            if not rows:
                print("Tidak ada user terdaftar.")
            else:
                print("=== Daftar User ===")
                for r in rows:
                    print(f"[{r['id']}] {r['username']} | role: {r['role']} | dibuat: {r['created_at']}")
            sys.exit(0)

        if "--fix-admin" in sys.argv:
            clear_screen()
            print("=== Pengaturan admin ===")
            username = input("Username admin yang ingin disetel: ").strip() or "admin"
            pwd1 = input("Password baru: ")
            pwd2 = input("Ulangi password baru: ")
            if pwd1 != pwd2:
                print("Password tidak cocok. Gagal menyetel admin.")
                sys.exit(1)
            auth.upsert_admin(username, pwd1)
            print(f"Akun admin '{username}' berhasil disetel/diperbarui.")
            print("Sekarang jalankan aplikasi tanpa --fix-admin lalu login admin.")
            sys.exit(0)

        # Jalankan CLI
        CLI(auth, books, loans, user_repo).run()
    except KeyboardInterrupt:
        print("\nDihentikan oleh pengguna.")
        sys.exit(0)