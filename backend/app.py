"""
GlobeTrotter Yaoundé — Phase 1 (Monolith)
Flask + JSON file storage. Single-server REST API + static frontend hosting.
No AI, no OAuth — email/password registration only, scoped to Yaoundé (20 places).
"""
import json
import os
import time
import uuid
import hashlib
import hmac
import base64
from functools import wraps
from flask import Flask, jsonify, request, send_from_directory, g

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

app = Flask(__name__, static_folder=None)

SECRET = "yaounde-seven-hills-dev-secret"  # dev-only signing key for demo tokens

# ---------------------------------------------------------------------------
# tiny JSON "database" helpers
# ---------------------------------------------------------------------------

def _path(name):
    return os.path.join(DATA_DIR, f"{name}.json")


def read_db(name):
    with open(_path(name), "r", encoding="utf-8") as f:
        return json.load(f)


def write_db(name, data):
    tmp = _path(name) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path(name))


def next_id(rows):
    return (max((r["id"] for r in rows), default=0)) + 1


# ---------------------------------------------------------------------------
# minimal signed-token auth (JWT-style, no external dependency)
# ---------------------------------------------------------------------------

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


def hash_password(password, salt=None):
    salt = salt or uuid.uuid4().hex
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${digest.hex()}"


def check_password(password, stored):
    salt, _ = stored.split("$")
    return hmac.compare_digest(hash_password(password, salt), stored)


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


# ---------------------------------------------------------------------------
# static frontend
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    full = os.path.join(FRONTEND_DIR, filename)
    if os.path.isfile(full):
        return send_from_directory(FRONTEND_DIR, filename)
    return send_from_directory(FRONTEND_DIR, "index.html")


# ---------------------------------------------------------------------------
# auth endpoints
# ---------------------------------------------------------------------------

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

    users = read_db("users")
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
    write_db("users", users)

    token = make_token(user["id"], user["email"])
    return jsonify({"token": token, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}), 201


@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json(force=True, silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    users = read_db("users")
    user = next((u for u in users if u["email"] == email), None)
    if not user or not check_password(password, user["password"]):
        return jsonify({"error": "Email ou mot de passe incorrect"}), 401

    token = make_token(user["id"], user["email"])
    return jsonify({"token": token, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}})


@app.route("/api/me")
@login_required
def me():
    users = read_db("users")
    user = next((u for u in users if u["id"] == g.user["uid"]), None)
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    return jsonify({"id": user["id"], "name": user["name"], "email": user["email"],
                     "preferences": user.get("preferences", [])})


# ---------------------------------------------------------------------------
# destinations / places
# ---------------------------------------------------------------------------

@app.route("/api/places")
def list_places():
    places = read_db("places")
    q = (request.args.get("q") or "").strip().lower()
    category = request.args.get("category")
    max_price = request.args.get("max_price", type=int)

    results = places
    if q:
        results = [p for p in results if q in p["name"].lower()
                   or q in p["description"].lower()
                   or q in p["quartier"].lower()
                   or any(q in t for t in p["tags"])]
    if category and category != "all":
        results = [p for p in results if p["category"] == category]
    if max_price is not None:
        results = [p for p in results if p["price_level"] <= max_price]

    return jsonify({"count": len(results), "places": results})


@app.route("/api/places/<int:place_id>")
def get_place(place_id):
    places = read_db("places")
    place = next((p for p in places if p["id"] == place_id), None)
    if not place:
        return jsonify({"error": "Lieu introuvable"}), 404
    reviews = [r for r in read_db("reviews") if r["place_id"] == place_id]
    return jsonify({"place": place, "reviews": reviews})


@app.route("/api/categories")
def categories():
    places = read_db("places")
    cats = sorted({p["category"] for p in places})
    return jsonify({"categories": cats})


# ---------------------------------------------------------------------------
# recommendations — based on preferences, popularity (rating), favorites
# ---------------------------------------------------------------------------

@app.route("/api/recommendations")
@optional_auth
def recommendations():
    places = read_db("places")
    preferred_tags = set()

    if g.user:
        users = read_db("users")
        user = next((u for u in users if u["id"] == g.user["uid"]), None)
        if user:
            preferred_tags = set(user.get("preferences", []))
        favs = [f["place_id"] for f in read_db("favorites") if f["user_id"] == g.user["uid"]]
        fav_categories = {p["category"] for p in places if p["id"] in favs}
        for p in places:
            if p["category"] in fav_categories:
                preferred_tags.update(p["tags"])

    def score(p):
        s = p["rating"]
        if preferred_tags:
            s += 2 * len(preferred_tags.intersection(p["tags"]))
        return s

    ranked = sorted(places, key=score, reverse=True)
    return jsonify({"places": ranked[:8], "personalized": bool(preferred_tags)})


# ---------------------------------------------------------------------------
# favorites
# ---------------------------------------------------------------------------

@app.route("/api/favorites", methods=["GET"])
@login_required
def list_favorites():
    favs = [f for f in read_db("favorites") if f["user_id"] == g.user["uid"]]
    places = read_db("places")
    place_ids = {f["place_id"] for f in favs}
    return jsonify({"places": [p for p in places if p["id"] in place_ids]})


@app.route("/api/favorites/<int:place_id>", methods=["POST"])
@login_required
def add_favorite(place_id):
    favs = read_db("favorites")
    if not any(f["user_id"] == g.user["uid"] and f["place_id"] == place_id for f in favs):
        favs.append({"user_id": g.user["uid"], "place_id": place_id})
        write_db("favorites", favs)
    return jsonify({"ok": True})


@app.route("/api/favorites/<int:place_id>", methods=["DELETE"])
@login_required
def remove_favorite(place_id):
    favs = read_db("favorites")
    favs = [f for f in favs if not (f["user_id"] == g.user["uid"] and f["place_id"] == place_id)]
    write_db("favorites", favs)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# itineraries (trip planner)
# ---------------------------------------------------------------------------

@app.route("/api/itineraries", methods=["GET"])
@login_required
def list_itineraries():
    trips = [t for t in read_db("itineraries") if t["user_id"] == g.user["uid"]]
    return jsonify({"itineraries": trips})


@app.route("/api/itineraries", methods=["POST"])
@login_required
def create_itinerary():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip() or "Mon voyage à Yaoundé"
    start_date = body.get("start_date")
    end_date = body.get("end_date")
    place_ids = body.get("place_ids") or []

    trips = read_db("itineraries")
    places = {p["id"]: p for p in read_db("places")}
    estimated_budget = sum(2000 + places[pid]["price_level"] * 5000 for pid in place_ids if pid in places)

    trip = {
        "id": next_id(trips),
        "user_id": g.user["uid"],
        "name": name,
        "start_date": start_date,
        "end_date": end_date,
        "place_ids": place_ids,
        "estimated_budget_fcfa": estimated_budget,
        "share_code": uuid.uuid4().hex[:8],
        "created_at": int(time.time()),
    }
    trips.append(trip)
    write_db("itineraries", trips)
    return jsonify({"itinerary": trip}), 201


@app.route("/api/itineraries/<int:trip_id>", methods=["PUT"])
@login_required
def update_itinerary(trip_id):
    body = request.get_json(force=True, silent=True) or {}
    trips = read_db("itineraries")
    trip = next((t for t in trips if t["id"] == trip_id and t["user_id"] == g.user["uid"]), None)
    if not trip:
        return jsonify({"error": "Itinéraire introuvable"}), 404
    for field in ("name", "start_date", "end_date", "place_ids"):
        if field in body:
            trip[field] = body[field]
    if "place_ids" in body:
        places = {p["id"]: p for p in read_db("places")}
        trip["estimated_budget_fcfa"] = sum(
            2000 + places[pid]["price_level"] * 5000 for pid in trip["place_ids"] if pid in places
        )
    write_db("itineraries", trips)
    return jsonify({"itinerary": trip})


@app.route("/api/itineraries/<int:trip_id>", methods=["DELETE"])
@login_required
def delete_itinerary(trip_id):
    trips = read_db("itineraries")
    trips = [t for t in trips if not (t["id"] == trip_id and t["user_id"] == g.user["uid"])]
    write_db("itineraries", trips)
    return jsonify({"ok": True})


@app.route("/api/share/<share_code>")
def shared_itinerary(share_code):
    trips = read_db("itineraries")
    trip = next((t for t in trips if t["share_code"] == share_code), None)
    if not trip:
        return jsonify({"error": "Lien de partage invalide"}), 404
    places = {p["id"]: p for p in read_db("places")}
    trip_places = [places[pid] for pid in trip["place_ids"] if pid in places]
    return jsonify({"itinerary": trip, "places": trip_places})


# ---------------------------------------------------------------------------
# reviews
# ---------------------------------------------------------------------------

@app.route("/api/places/<int:place_id>/reviews", methods=["POST"])
@login_required
def add_review(place_id):
    body = request.get_json(force=True, silent=True) or {}
    rating = body.get("rating")
    comment = (body.get("comment") or "").strip()
    if not isinstance(rating, (int, float)) or not (1 <= rating <= 5):
        return jsonify({"error": "La note doit être comprise entre 1 et 5"}), 400

    users = {u["id"]: u for u in read_db("users")}
    reviews = read_db("reviews")
    review = {
        "id": next_id(reviews),
        "place_id": place_id,
        "user_id": g.user["uid"],
        "author": users.get(g.user["uid"], {}).get("name", "Voyageur"),
        "rating": rating,
        "comment": comment,
        "created_at": int(time.time()),
    }
    reviews.append(review)
    write_db("reviews", reviews)
    return jsonify({"review": review}), 201


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
