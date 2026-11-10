import base64
import hashlib
import hmac
from datetime import timedelta

import jwt
from cryptography.fernet import Fernet
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.core.db import utcnow

_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _hasher.verify(password, hashed)


def password_fingerprint(password_hash: str) -> str:
    """Changes whenever the password does: sessions and reset links carry it and die with it."""
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def session_token(user) -> str:
    return create_token(str(user.id), pv=password_fingerprint(user.password_hash))


def create_token(subject: str, minutes: int | None = None, **claims) -> str:
    s = get_settings()
    exp = utcnow() + timedelta(minutes=minutes or s.access_token_minutes)
    return jwt.encode({"sub": subject, "exp": exp, **claims}, s.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])


def _fernet() -> Fernet:
    s = get_settings()
    key = (
        s.token_encryption_key
        or base64.urlsafe_b64encode(hashlib.sha256(s.secret_key.encode()).digest()).decode()
    )
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()


def verify_meta_signature(body: bytes, header: str | None) -> bool:
    """Validate X-Hub-Signature-256 = sha256=HMAC(app_secret, raw_body)."""
    secret = get_settings().meta_app_secret
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))
