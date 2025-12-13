import sqlite3
from entities import User
from services import AuthService, BookService, LoanService, UserRepository
from utils import clear_screen, pause

class CLI:
    def __init__(self, auth: AuthService, books: BookService, loans: LoanService, user_repo: UserRepository):
        self.auth = auth
        self.books = books
        self.loans = loans
        self.user_repo = user_repo

    def run(self):
        while True:
            clear_screen()
            print("=== Sistem Perpustakaan ===")
            print("1. Lihat semua buku")
            print("2. Lihat buku tersedia")
            print("3. Cari buku")
            print("4. Registrasi")
            print("5. Login Pengunjung")
            print("6. Login Admin")
            print("7. Pengaturan Admin")
            print("8. Keluar")
            c = input("Pilih menu: ").strip()
            try:
                if c == "1":
                    self.ui_list_all()
                elif c == "2":
                    self.ui_list_available()
                elif c == "3":
                    self.ui_search()
                elif c == "4":
                    self.ui_register()
                elif c == "5":
                    self.ui_login_user()
                elif c == "6":
                    self.ui_login_admin()
                elif c == "7":
                    self.ui_fix_admin()
                elif c == "8":
                    print("Sampai jumpa!")
                    break
                else:
                    print("Pilihan tidak valid.")
                    pause()
            except ValueError as e:
                print(str(e))
                pause()

    def ui_list_all(self):
        clear_screen()
        rows = self.books.list_all()
        print("=== Daftar Buku ===")
        if not rows:
            print("Belum ada buku.")
        for r in rows:
            print(f"[{r['id']}] {r['title']} - {r['author']} ({r['year']}) | Tersedia: {r['copies_available']}/{r['copies_total']}")
        pause()

    def ui_list_available(self):
        clear_screen()
        rows = self.books.list_available()
        print("=== Buku Tersedia ===")
        if not rows:
            print("Tidak ada buku tersedia.")
        for r in rows:
            print(f"[{r['id']}] {r['title']} - {r['author']} ({r['year']}) | Tersedia: {r['copies_available']}/{r['copies_total']}")
        pause()

    def ui_search(self):
        clear_screen()
        print("=== Cari Buku ===")
        q = input("Masukkan judul/penulis: ").strip()
        rows = self.books.search(q)
        if not rows:
            print("Tidak ada hasil.")
        for r in rows:
            print(f"[{r['id']}] {r['title']} - {r['author']} ({r['year']}) | Tersedia: {r['copies_available']}/{r['copies_total']}")
        pause()

    def ui_register(self):
        clear_screen()
        print("=== Registrasi Pengguna ===")
        u = input("Username: ").strip()
        p1 = input("Password: ")
        p2 = input("Ulangi Password: ")
        if not u:
            print("Username tidak boleh kosong")
        elif p1 != p2:
            print("Password tidak cocok")
        elif len(p1) < 6:
            print("Password minimal 6 karakter")
        else:
            try:
                self.auth.register(u, p1)
                print("Registrasi berhasil! Silakan login.")
            except sqlite3.IntegrityError:
                print("Username sudah terdaftar.")
        pause()

    def ui_login_user(self):
        clear_screen()
        print("=== Login Pengunjung ===")
        u = input("Username: ").strip()
        p = input("Password: ")
        user = self.auth.login(u, p)
        if not user:
            print("Login gagal")
            pause()
            return
        if user.is_admin():
            self.admin_menu(user)
        else:
            self.user_menu(user)

    def ui_login_admin(self):
        clear_screen()
        print("=== Login Admin ===")
        u = input("Username Admin: ").strip()
        p = input("Password: ")
        user = self.auth.login(u, p)
        if not user or not user.is_admin():
            print("Login admin gagal. Periksa username/password admin.")
            pause()
            return
        self.admin_menu(user)

    def ui_fix_admin(self):
        clear_screen()
        print("=== Pengaturan Admin ===")
        u = input("Username admin: ").strip() or "admin"
        p1 = input("Password baru: ")
        p2 = input("Ulangi password baru: ")
        if p1 != p2:
            print("Password tidak cocok.")
            pause()
            return
        self.auth.upsert_admin(u, p1)
        print(f"Akun admin '{u}' berhasil disetel/diperbarui.")
        pause("Tekan Enter untuk masuk sebagai admin...")
        user = self.auth.login(u, p1)
        if user and user.is_admin():
            self.admin_menu(user)

    def admin_menu(self, user: User):
        while True:
            clear_screen()
            print(f"=== Menu Admin (Login: {user.username}) ===")
            print("1. Lihat semua buku")
            print("2. Cari buku")
            print("3. Tambah buku")
            print("4. Ubah stok buku")
            print("5. Hapus buku")
            print("6. Logout")
            c = input("Pilih menu: ").strip()
            try:
                if c == "1":
                    self.ui_list_all()
                elif c == "2":
                    self.ui_search()
                elif c == "3":
                    self.ui_admin_add_book()
                elif c == "4":
                    self.ui_admin_update_stock()
                elif c == "5":
                    self.ui_admin_delete_book()
                elif c == "6":
                    break
                else:
                    print("Pilihan tidak valid.")
                    pause()
            except ValueError as e:
                print(str(e))
                pause()

    def user_menu(self, user: User):
        while True:
            clear_screen()
            print(f"=== Menu Pengunjung (Login: {user.username}) ===")
            print("1. Lihat semua buku")
            print("2. Lihat buku tersedia")
            print("3. Cari buku")
            print("4. Pinjam buku")
            print("5. Kembalikan buku")
            print("6. Riwayat peminjaman")
            print("7. Logout")
            c = input("Pilih menu: ").strip()
            try:
                if c == "1":
                    self.ui_list_all()
                elif c == "2":
                    self.ui_list_available()
                elif c == "3":
                    self.ui_search()
                elif c == "4":
                    self.ui_user_borrow(user)
                elif c == "5":
                    self.ui_user_return(user)
                elif c == "6":
                    self.ui_user_history(user)
                elif c == "7":
                    break
                else:
                    print("Pilihan tidak valid.")
                    pause()
            except ValueError as e:
                print(str(e))
                pause()

    def ui_admin_add_book(self):
        clear_screen()
        print("=== Admin: Tambah Buku ===")
        title = input("Judul: ").strip()
        author = input("Penulis: ").strip()
        year = input("Tahun (angka, opsional): ").strip()
        copies = input("Jumlah eksemplar: ").strip()
        if not title or not author or not copies.isdigit():
            print("Input tidak valid.")
            pause()
            return
        self.books.add(title, author, int(year) if year.isdigit() else None, int(copies))
        print("Buku berhasil ditambahkan.")
        pause()

    def ui_admin_update_stock(self):
        clear_screen()
        self.ui_list_all()
        try:
            book_id = int(input("Masukkan ID buku: ").strip())
            new_total = int(input("Total eksemplar baru: ").strip())
            self.books.update_stock(book_id, new_total)
            print("Stok buku diperbarui.")
        except ValueError as e:
            print(str(e))
        pause()

    def ui_admin_delete_book(self):
        clear_screen()
        self.ui_list_all()
        try:
            book_id = int(input("Masukkan ID buku: ").strip())
            self.books.delete(book_id)
            print("Buku berhasil dihapus.")
        except ValueError as e:
            print(str(e))
        pause()

    def ui_user_borrow(self, user: User):
        clear_screen()
        self.ui_list_available()
        try:
            book_id = int(input("Masukkan ID buku yang ingin dipinjam: ").strip())
            self.loans.borrow(user, book_id)
            print("Peminjaman berhasil. Batas pengembalian 7 hari dari sekarang.")
        except ValueError as e:
            print(str(e))
        pause()

    def ui_user_return(self, user: User):
        clear_screen()
        rows = self.loans.active_loans_by_user(user)
        if not rows:
            print("Tidak ada buku yang sedang Anda pinjam.")
            pause()
            return
        for r in rows:
            print(f"[{r['loan_id']}] {r['title']} - {r['author']} | Dipinjam: {r['loan_date']} | Jatuh tempo: {r['due_date']}")
        try:
            loan_id = int(input("Masukkan ID peminjaman yang ingin dikembalikan: ").strip())
            self.loans.return_book(user, loan_id)
            print("Pengembalian berhasil.")
        except ValueError as e:
            print(str(e))
        pause()

    def ui_user_history(self, user: User):
        clear_screen()
        rows = self.loans.history_by_user(user)
        if not rows:
            print("Belum ada riwayat peminjaman.")
        else:
            for r in rows:
                status = "Dikembalikan" if r["return_date"] else "Dipinjam"
                print(f"{r['title']} - {r['author']} | Pinjam: {r['loan_date']} | Jatuh tempo: {r['due_date']} | Status: {status}")
        pause()