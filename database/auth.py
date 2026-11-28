"""Minimal role-based access for the admin area (single admin role).

Set PIRS_ADMIN_USER and PIRS_ADMIN_PASSWORD_HASH in .env. Create a hash with:
    python -m database.auth "your-password"
"""
import hashlib
import hmac
import os
import secrets
import sys

ITERATIONS = 200_000


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"pbkdf2${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt, digest = stored.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iters)).hex()
        return hmac.compare_digest(calc, digest)
    except Exception:
        return False


def admin_configured() -> bool:
    return bool(os.getenv("PIRS_ADMIN_PASSWORD_HASH"))


def check_admin(username: str, password: str) -> bool:
    if not admin_configured():
        return False
    user_ok = hmac.compare_digest(username, os.getenv("PIRS_ADMIN_USER", "admin"))
    return verify_password(password, os.environ["PIRS_ADMIN_PASSWORD_HASH"]) and user_ok


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage: python -m database.auth "your-password"')
    print(f"PIRS_ADMIN_PASSWORD_HASH={hash_password(sys.argv[1])}")
