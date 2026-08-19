# GlobeTrotter Yaoundé — Phase 2 (Microservices)

Le monolithe de la Phase 1 est décomposé en **trois microservices indépendants**
plus une **API Gateway**, exactement selon l'architecture du cours :

```
                    Navigateur
                        │
                 API Gateway (5000)
                        │  sert aussi le frontend statique
        ┌───────────────┼────────────────┐
        │                │                │
  User Service    Itinerary Service  Recommendation Service
     (5001)            (5002)              (5003)
        │                │                │
   users.json      itineraries.json   places.json
                    favorites.json    (30 lieux)
                    reviews.json
```

Chaque service a **son propre processus Flask et son propre stockage JSON** —
aucune base de données partagée. Les services communiquent entre eux par de
**vrais appels HTTP synchrones** (bibliothèque `requests`) :

- `recommendation-service` interroge `user-service` (`GET /api/me`) pour les
  préférences de l'utilisateur, et `itinerary-service`
  (`GET /internal/favorites/<user_id>`) pour ses favoris, afin de calculer des
  recommandations personnalisées.
- `itinerary-service` interroge `recommendation-service`
  (`GET /internal/places?ids=...`) pour connaître le prix des lieux et calculer
  le budget estimé d'un voyage.
- `itinerary-service` interroge `user-service` (`GET /api/me`) pour attacher le
  nom de l'auteur à un avis.

L'**API Gateway** est le seul point d'entrée pour le navigateur : elle route
chaque appel `/api/...` vers le microservice propriétaire de cette donnée, et
sert aussi les fichiers statiques du frontend (`frontend/`).

## Lancer le projet

### Option A — avec Docker (recommandé pour Phase 2)

```bash
docker compose up --build
```

Cela construit et démarre les quatre conteneurs (`user-service`,
`itinerary-service`, `recommendation-service`, `api-gateway`) sur leur propre
réseau Docker : les services s'appellent entre eux par leur nom de conteneur
(`http://user-service:5001`, etc.) au lieu de `localhost`, ce qui est
configuré via les variables d'environnement dans `docker-compose.yml`. Les
dossiers `data/` de chaque service sont montés en volume, donc vos données
persistent entre deux `docker compose up`.

Ouvrez ensuite **http://localhost:5000**. Pour tout arrêter :
`docker compose down` (ajoutez `-v` pour aussi supprimer les données).

### Option B — sans Docker, en Python directement

Tout lancer d'un coup :

```bash
pip install -r requirements.txt
python run_all.py
```

Ou un terminal par service (utile pour observer chaque service séparément) :

```bash
cd services/user-service && python app.py            # port 5001
cd services/itinerary-service && python app.py        # port 5002
cd services/recommendation-service && python app.py   # port 5003
cd services/api-gateway && python app.py               # port 5000
```

Dans les deux cas, vérifiez que tout est en ligne avec
`GET http://localhost:5000/gateway/health`.

## Nouveautés de la Phase 2

- **30 lieux** (20 initiaux + 10 nouveaux : Stade Ahmadou Ahidjo, Aéroport de
  Nsimalen, Gare de Yaoundé, Basilique de Mvolyé, Santa Lucia Mall, Canal
  Olympia, Village Artisanal, Zoo de Mvog-Betsi, Institut Français, immeuble
  de la BEAC), répartis sur 16 catégories.
- **Photos réseau réelles** : chaque fiche essaie de charger une vraie photo
  du lieu depuis Wikipédia (via son API publique, sans clé requise) et ne
  retombe sur une image de remplacement stable que si aucune photo n'est
  trouvée.
- **Sélecteur de langue FR/EN** dans la barre de navigation (bouton à côté du
  thème) : traduit l'interface (menus, boutons, titres) et bascule les
  descriptions des lieux vers leur version anglaise quand elle existe.
- Toutes les fonctionnalités de la Phase 1 restent disponibles : recherche et
  filtres, carte OpenStreetMap 3D, itinéraire routier depuis la position du
  visiteur (OSRM), favoris, avis, planificateur de voyage avec budget estimé
  et lien de partage.

## Défis rencontrés (voir aussi le support de cours)

- **Latence réseau** : chaque recommandation personnalisée déclenche
  désormais deux appels HTTP supplémentaires (vers user-service et
  itinerary-service) — sensible mais mesuré et acceptable en local.
- **Cohérence des données** : les 30 lieux n'existent que dans
  `recommendation-service` ; les deux autres services ne stockent que des
  identifiants et interrogent ce service pour les détails, pour éviter toute
  divergence.
- **Découverte de service** : simplifiée ici via des URLs configurables par
  variables d'environnement (`USER_SERVICE_URL`, `ITINERARY_SERVICE_URL`,
  `RECOMMENDATION_SERVICE_URL`) — `localhost:<port>` en local, noms de
  conteneurs Docker (`http://user-service:5001`, etc.) avec `docker compose`
  — une vraie registry (Consul, etc.) serait l'étape suivante en Phase 3/4.
- **Débogage distribué** : chaque service journalise indépendamment
  (`user.log`, `itinerary.log`, `reco.log`, `gateway.log` si vous utilisez
  `run_all.py`), ce qui rend le suivi d'une requête à travers les services
  plus difficile qu'avec le monolithe de la Phase 1.
