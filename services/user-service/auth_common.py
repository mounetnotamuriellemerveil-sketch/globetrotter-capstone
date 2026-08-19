"""Shared signed-token auth (JWT-style, no external dependency).
Copied into each microservice so every process can issue/verify tokens
independently without a shared session store — this is the same SECRET
across services, which is what lets any of them trust a token minted by
user-service.
"""
import json
import time
import hmac
import hashlib
import base64
from functools import wraps
from flask import request, jsonify, g

SECRET = "yaounde-seven-hills-dev-secret"  # dev-only signing key for demo tokens


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def make_token(user_id, email):
    payload = {"uid": user_id, "email": email, "iat": int(time.time())}
    body = _b64(json.dumps(payload).encode())
    sig = _b64(hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify_token(token):
    try:
        body, sig = token.split(".")
        expected = _b64(hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        return json.loads(_unb64(body))
    except Exception:
        return None


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Authentification requise"}), 401
        payload = verify_token(auth[7:])
        if not payload:
            return jsonify({"error": "Session invalide, reconnectez-vous"}), 401
        g.user = payload
        return f(*args, **kwargs)
    return wrapper


def optional_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        g.user = None
        if auth.startswith("Bearer "):
            g.user = verify_token(auth[7:])
        return f(*args, **kwargs)
    return wrapper


def hash_password(password, salt=None):
    import uuid
    salt = salt or uuid.uuid4().hex
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${digest.hex()}"


def check_password(password, stored):
    salt, _ = stored.split("$")
    return hmac.compare_digest(hash_password(password, salt), stored)
