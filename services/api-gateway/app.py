"""
GlobeTrotter Yaoundé — Phase 2 · API Gateway (port 5000)
Single entry point for all client requests. Serves the static frontend and
reverse-proxies every /api/* call to the microservice that owns that data,
so the browser only ever talks to one origin.
"""
import os
import requests
from flask import Flask, request, jsonify, send_from_directory, Response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.environ.get("FRONTEND_DIR") or os.path.abspath(os.path.join(BASE_DIR, "..", "..", "frontend"))

USER_SERVICE = os.environ.get("USER_SERVICE_URL", "http://localhost:5001")
ITINERARY_SERVICE = os.environ.get("ITINERARY_SERVICE_URL", "http://localhost:5002")
RECOMMENDATION_SERVICE = os.environ.get("RECOMMENDATION_SERVICE_URL", "http://localhost:5003")

app = Flask(__name__, static_folder=None)


def route_for(subpath: str) -> str:
    """Decide which microservice owns a given /api/<subpath> request."""
    if subpath.startswith("register") or subpath.startswith("login") or subpath.startswith("me"):
        return USER_SERVICE
    if subpath.startswith("favorites") or subpath.startswith("itineraries") or subpath.startswith("share"):
        return ITINERARY_SERVICE
    if "/reviews" in subpath:  # /places/<id>/reviews lives on itinerary-service
        return ITINERARY_SERVICE
    if subpath.startswith("places") or subpath.startswith("categories") or subpath.startswith("recommendations"):
        return RECOMMENDATION_SERVICE
    return None


@app.route("/api/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE"])
def gateway(subpath):
    target = route_for(subpath)
    if not target:
        return jsonify({"error": "Route API inconnue"}), 404

    url = f"{target}/api/{subpath}"
    try:
        upstream = requests.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers if k.lower() not in ("host", "content-length")},
            params=request.args,
            data=request.get_data(),
            timeout=8,
        )
    except requests.RequestException:
        return jsonify({"error": "Service indisponible pour le moment. Vérifiez que tous les microservices sont démarrés."}), 502

    excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    headers = [(k, v) for k, v in upstream.headers.items() if k.lower() not in excluded]
    return Response(upstream.content, status=upstream.status_code, headers=headers)


@app.route("/gateway/health")
def gateway_health():
    services = {"user-service": USER_SERVICE, "itinerary-service": ITINERARY_SERVICE, "recommendation-service": RECOMMENDATION_SERVICE}
    status = {}
    for name, base in services.items():
        try:
            r = requests.get(f"{base}/health", timeout=2)
            status[name] = "up" if r.ok else "erreur"
        except requests.RequestException:
            status[name] = "hors ligne"
    return jsonify(status)


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


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
