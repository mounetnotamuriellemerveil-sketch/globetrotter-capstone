"""
Launches all four Phase 2 services together for local development:
user-service (5001), itinerary-service (5002), recommendation-service (5003),
api-gateway (5000). Press Ctrl+C to stop everything.
"""
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
SERVICES = [
    ("user-service", "services/user-service/app.py"),
    ("itinerary-service", "services/itinerary-service/app.py"),
    ("recommendation-service", "services/recommendation-service/app.py"),
    ("api-gateway", "services/api-gateway/app.py"),
]

procs = []
try:
    for name, rel_path in SERVICES:
        path = os.path.join(BASE, rel_path)
        print(f"Démarrage de {name}...")
        procs.append((name, subprocess.Popen([sys.executable, path])))
        time.sleep(0.6)  # small stagger so ports bind cleanly

    print("\nTous les services tournent. Ouvrez http://localhost:5000")
    print("Ctrl+C pour tout arrêter.\n")
    for _, p in procs:
        p.wait()
except KeyboardInterrupt:
    print("\nArrêt des services...")
    for name, p in procs:
        p.terminate()
