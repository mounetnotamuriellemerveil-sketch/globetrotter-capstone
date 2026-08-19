"""
GlobeTrotter Yaoundé — Phase 2 · User Service (port 5001)
Owns the "users" data: registration, login, profile, preferences.
Runs as its own independent process with its own JSON store.
"""
import json
import os
import time
from flask import Flask, jsonify, request, g
from auth_common import make_token, login_required, hash_password, check_password

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

app = Flask(__name__)


def read_db():
    with open(os.path.join(DATA_DIR, "users.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def write_db(data):
    path = os.path.join(DATA_DIR, "users.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def next_id(rows):
    return (max((r["id"] for r in rows), default=0)) + 1


@app.route("/health")
def health():
    return jsonify({"service": "user-service", "status": "ok"})


@app.route("/api/register", methods=["POST"])
def register():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Nom, email et mot de passe sont requis"}), 400
    if len(password) < 6:
        return jsonify({"error": "Le mot de passe doit contenir au moins 6 caractères"}), 400

    users = read_db()
    if any(u["email"] == email for u in users):
        return jsonify({"error": "Un compte existe déjà avec cet email"}), 409

    user = {
        "id": next_id(users),
        "name": name,
        "email": email,
        "password": hash_password(password),
        "preferences": body.get("preferences") or [],
        "created_at": int(time.time()),
    }
    users.append(user)
    write_db(users)

    token = make_token(user["id"], user["email"])
    return jsonify({"token": token, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}), 201


@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json(force=True, silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    users = read_db()
    user = next((u for u in users if u["email"] == email), None)
    if not user or not check_password(password, user["password"]):
        return jsonify({"error": "Email ou mot de passe incorrect"}), 401

    token = make_token(user["id"], user["email"])
    return jsonify({"token": token, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}})


@app.route("/api/me")
@login_required
def me():
    users = read_db()
    user = next((u for u in users if u["id"] == g.user["uid"]), None)
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    return jsonify({"id": user["id"], "name": user["name"], "email": user["email"],
                     "preferences": user.get("preferences", [])})


# internal endpoint — called by recommendation-service to read a user's
# preferences without needing the user's own bearer token forwarded
@app.route("/internal/users/<int:user_id>/preferences")
def internal_preferences(user_id):
    users = read_db()
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    return jsonify({"preferences": user.get("preferences", [])})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5001)
