"""
GlobeTrotter Yaoundé — Phase 2 · Itinerary Service (port 5002)
Owns the "itineraries", "favorites" and "reviews" data.
Talks to recommendation-service over real HTTP to price a trip's places
and to attach place names to favorites — a genuine inter-service call,
not a shared database.
"""
import json
import os
import time
import uuid
from flask import Flask, jsonify, request, g
import requests
from auth_common import login_required

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RECOMMENDATION_SERVICE = os.environ.get("RECOMMENDATION_SERVICE_URL", "http://localhost:5003")

app = Flask(__name__)


def read_db(name):
    with open(os.path.join(DATA_DIR, f"{name}.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def write_db(name, data):
    path = os.path.join(DATA_DIR, f"{name}.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def next_id(rows):
    return (max((r["id"] for r in rows), default=0)) + 1


def fetch_places(place_ids):
    """Real synchronous REST call to recommendation-service for place details."""
    if not place_ids:
        return {}
    try:
        res = requests.get(f"{RECOMMENDATION_SERVICE}/internal/places", params={"ids": ",".join(map(str, place_ids))}, timeout=4)
        res.raise_for_status()
        return {p["id"]: p for p in res.json().get("places", [])}
    except requests.RequestException:
        return {}


@app.route("/health")
def health():
    return jsonify({"service": "itinerary-service", "status": "ok"})


# ---------------------------------------------------------------------------
# favorites
# ---------------------------------------------------------------------------

@app.route("/api/favorites", methods=["GET"])
@login_required
def list_favorites():
    favs = [f for f in read_db("favorites") if f["user_id"] == g.user["uid"]]
    places = fetch_places([f["place_id"] for f in favs])
    return jsonify({"places": [places[f["place_id"]] for f in favs if f["place_id"] in places]})


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


# internal endpoint — recommendation-service reads a user's favorite
# categories to personalize scoring
@app.route("/internal/favorites/<int:user_id>")
def internal_favorites(user_id):
    favs = [f["place_id"] for f in read_db("favorites") if f["user_id"] == user_id]
    return jsonify({"place_ids": favs})


# ---------------------------------------------------------------------------
# itineraries
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
    place_ids = body.get("place_ids") or []

    places = fetch_places(place_ids)
    estimated_budget = sum(2000 + places[pid]["price_level"] * 5000 for pid in place_ids if pid in places)

    trips = read_db("itineraries")
    trip = {
        "id": next_id(trips),
        "user_id": g.user["uid"],
        "name": name,
        "start_date": body.get("start_date"),
        "end_date": body.get("end_date"),
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
        places = fetch_places(trip["place_ids"])
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
    places = fetch_places(trip["place_ids"])
    return jsonify({"itinerary": trip, "places": [places[pid] for pid in trip["place_ids"] if pid in places]})


# ---------------------------------------------------------------------------
# reviews
# ---------------------------------------------------------------------------

@app.route("/api/places/<int:place_id>/reviews", methods=["GET"])
def get_reviews(place_id):
    reviews = [r for r in read_db("reviews") if r["place_id"] == place_id]
    return jsonify({"reviews": reviews})


USER_SERVICE = os.environ.get("USER_SERVICE_URL", "http://localhost:5001")


@app.route("/api/places/<int:place_id>/reviews", methods=["POST"])
@login_required
def add_review(place_id):
    body = request.get_json(force=True, silent=True) or {}
    rating = body.get("rating")
    comment = (body.get("comment") or "").strip()
    if not isinstance(rating, (int, float)) or not (1 <= rating <= 5):
        return jsonify({"error": "La note doit être comprise entre 1 et 5"}), 400

    # real inter-service call: ask user-service for the reviewer's display name
    author = "Voyageur"
    try:
        res = requests.get(f"{USER_SERVICE}/api/me", headers={"Authorization": request.headers.get("Authorization", "")}, timeout=3)
        if res.ok:
            author = res.json().get("name", author)
    except requests.RequestException:
        pass

    reviews = read_db("reviews")
    review = {
        "id": next_id(reviews),
        "place_id": place_id,
        "user_id": g.user["uid"],
        "author": author,
        "rating": rating,
        "comment": comment,
        "created_at": int(time.time()),
    }
    reviews.append(review)
    write_db("reviews", reviews)
    return jsonify({"review": review}), 201


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5002)
