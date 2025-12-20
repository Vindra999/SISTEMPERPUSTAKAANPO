import os
import hashlib
import hmac
import binascii


class PasswordHasher:
    """Simple, safer password hasher using PBKDF2-HMAC-SHA256 with per-password salt.

    Stored format: <salt_hex>$<hash_hex>
    """

    ITERATIONS = 100_000
    SALT_SIZE = 16

    def hash(self, password: str) -> str:
        salt = hashlib.sha256(os.urandom(self.SALT_SIZE)).digest()[: self.SALT_SIZE]
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, self.ITERATIONS
        )
        return f"{binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"

    def verify(self, hashed: str, password: str) -> bool:
        try:
            salt_hex, hash_hex = hashed.split("$", 1)
        except ValueError:
            return False
        salt = binascii.unhexlify(salt_hex)
        expected = binascii.unhexlify(hash_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, self.ITERATIONS)
        return hmac.compare_digest(dk, expected)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def pause(msg="Tekan Enter untuk melanjutkan..."):
    input(msg)
