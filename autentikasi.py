"""Kata sandi demo dan verifikasi kredensial lokal."""
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_bytes

ADMIN = "admin"
DEMO_PASSWORDS = {
    ADMIN: "AlabamaAdmin26!",
    "DM1": "AlabamaDM1-26!",
    "DM2": "AlabamaDM2-26!",
    "DM3": "AlabamaDM3-26!",
}
ITERATIONS = 600_000


def digest(password, salt):
    return pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS).hex()


def hash_password(password):
    salt = token_bytes(16)
    return f"{salt.hex()}:{digest(password, salt)}"


def authenticate(accounts, username, password):
    if len(username) > 100 or len(password) > 128:
        return None
    normalized = username.strip().casefold()
    code = next((key for key in accounts if key.casefold() == normalized), None)
    stored = accounts.get(code, f"{'0' * 32}:{'0' * 64}")
    salt, reference = stored.split(":")
    return code if compare_digest(digest(password, bytes.fromhex(salt)), reference) else None
