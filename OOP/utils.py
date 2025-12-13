import hashlib
import binascii
import os

class PasswordHasher:
    def hash(self, password: str) -> str:
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode("ascii")
        pwdhash = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, 100000)
        return (salt + binascii.hexlify(pwdhash)).decode("ascii")

    def verify(self, stored: str, provided: str) -> bool:
        salt = stored[:64]
        stored_hash = stored[64:]
        pwdhash = hashlib.pbkdf2_hmac(
            "sha512", provided.encode("utf-8"), salt.encode("ascii"), 100000
        )
        return binascii.hexlify(pwdhash).decode("ascii") == stored_hash

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def pause(msg="Tekan Enter untuk lanjut..."):
    try:
        input(msg)
    except EOFError:
        pass