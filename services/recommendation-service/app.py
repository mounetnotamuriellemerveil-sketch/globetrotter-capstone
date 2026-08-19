"""
GlobeTrotter Yaoundé — Phase 2 · Recommendation Service (port 5003)
Owns the "places" (destinations) data. Personalized recommendations are
computed by making real HTTP calls to user-service (preferences) and
itinerary-service (favorites) — exactly the "Recommendation Service reads
data from User and Itinerary services" wiring from the course slide.
"""
import json
import os
from flask import Flask, jsonify, request, g
import requests
from auth_common import optional_auth

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USER_SERVICE = os.environ.get("USER_SERVICE_URL", "http://localhost:5001")
ITINERARY_SERVICE = os.environ.get("ITINERARY_SERVICE_URL", "http://localhost:5002")

app = Flask(__name__)


def read_places():
    with open(os.path.join(DATA_DIR, "places.json"), "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/health")
def health():
    return jsonify({"service": "recommendation-service", "status": "ok"})


@app.route("/api/places")
def list_places():
    places = read_places()
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
    places = read_places()
    place = next((p for p in places if p["id"] == place_id), None)
    if not place:
        return jsonify({"error": "Lieu introuvable"}), 404
    return jsonify({"place": place})


@app.route("/api/categories")
def categories():
    places = read_places()
    cats = sorted({p["category"] for p in places})
    return jsonify({"categories": cats})


# internal endpoint — itinerary-service batches place lookups through this
# (e.g. to price a trip) instead of duplicating destination data
@app.route("/internal/places")
def internal_places():
    ids_param = request.args.get("ids", "")
    wanted = {int(x) for x in ids_param.split(",") if x.strip().isdigit()}
    places = read_places()
    return jsonify({"places": [p for p in places if p["id"] in wanted]})


@app.route("/api/recommendations")
@optional_auth
def recommendations():
    places = read_places()
    preferred_tags = set()
    personalized = False

    if g.user:
        auth_header = request.headers.get("Authorization", "")

        # real synchronous call #1 — ask user-service for this user's stated preferences
        try:
            res = requests.get(f"{USER_SERVICE}/api/me", headers={"Authorization": auth_header}, timeout=4)
            if res.ok:
                preferred_tags.update(res.json().get("preferences", []))
        except requests.RequestException:
            pass

        # real synchronous call #2 — ask itinerary-service for this user's favorites,
        # then infer more taste tags from the categories they favorited
        try:
            res = requests.get(f"{ITINERARY_SERVICE}/internal/favorites/{g.user['uid']}", timeout=4)
            if res.ok:
                fav_ids = set(res.json().get("place_ids", []))
                fav_categories = {p["category"] for p in places if p["id"] in fav_ids}
                for p in places:
                    if p["category"] in fav_categories:
                        preferred_tags.update(p["tags"])
        except requests.RequestException:
            pass

        personalized = bool(preferred_tags)

    def score(p):
        s = p["rating"]
        if preferred_tags:
            s += 2 * len(preferred_tags.intersection(p["tags"]))
        return s

    ranked = sorted(places, key=score, reverse=True)
    return jsonify({"places": ranked[:8], "personalized": personalized})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5003)
