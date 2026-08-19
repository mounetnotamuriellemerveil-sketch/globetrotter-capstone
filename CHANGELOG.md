# Changelog — GlobeTrotter Yaoundé

Toutes les versions notables de ce projet sont documentées ici.

## [2.1.0] — 2026-08-16

### Ajouté — Conteneurisation Docker
- `Dockerfile` pour chacun des quatre services (`user-service`,
  `itinerary-service`, `recommendation-service`, `api-gateway`).
- `docker-compose.yml` à la racine orchestrant les quatre conteneurs sur un
  réseau Docker commun ; les services se joignent par nom de conteneur
  (`http://user-service:5001`, etc.) plutôt que par `localhost`.
- Les services internes (`user-service`, `itinerary-service`,
  `recommendation-service`) écoutent désormais sur `0.0.0.0` (au lieu de
  `127.0.0.1`) pour être joignables depuis d'autres conteneurs.
- Les dossiers `data/` de chaque service sont montés en volume Docker, donc
  les données JSON persistent entre deux `docker compose up`.
- `.dockerignore` à la racine.
- `README.md` mis à jour avec les instructions `docker compose up --build`
  en plus du lancement Python direct (les deux méthodes restent supportées).

## [2.0.0] — 2026-08-16

### Ajouté — Phase 2 (Microservices)
- Décomposition du monolithe en **trois microservices indépendants** +
  une **API Gateway**, chacun avec son propre processus Flask et son propre
  stockage JSON, communiquant par de vrais appels HTTP (`requests`) :
  - `user-service` (5001) — registration/login/profil
  - `itinerary-service` (5002) — itinéraires, favoris, avis ; appelle
    `user-service` et `recommendation-service`
  - `recommendation-service` (5003) — les 30 lieux et les recommandations
    personnalisées ; appelle `user-service` et `itinerary-service`
  - `api-gateway` (5000) — point d'entrée unique, route chaque appel vers le
    bon service, sert aussi le frontend
- **10 nouveaux lieux** (30 au total) : Stade Ahmadou Ahidjo, Aéroport de
  Nsimalen, Gare de Yaoundé, Basilique de Mvolyé, Santa Lucia Mall, Canal
  Olympia, Village Artisanal, Zoo de Mvog-Betsi, Institut Français, immeuble
  de la BEAC — avec descriptions bilingues FR/EN.
- **Photos réseau réelles** des lieux, récupérées depuis l'API publique de
  Wikipédia, avec repli sur une image stable si aucune photo n'est trouvée.
- **Sélecteur de langue FR/EN** dans la barre de navigation, traduisant
  l'interface et les descriptions des lieux.
- `run_all.py` pour lancer les quatre services en une seule commande.
- Testé de bout en bout : inscription, recommandations personnalisées
  (appels croisés user-service + itinerary-service), ajout de favori,
  création d'itinéraire avec budget calculé via un appel à
  recommendation-service, avis avec nom d'auteur récupéré via user-service.

## [1.1.1] — 2026-08-16

### Rétabli
- Retour à l'authentification par **email + mot de passe** (formulaires
  `login.html` et `register.html`), suite à l'annulation de la connexion
  Google demandée juste après son ajout.
- Endpoints `POST /api/register` et `POST /api/login` restaurés dans
  `backend/app.py`, avec hachage de mot de passe (PBKDF2-HMAC-SHA256).

### Supprimé
- Endpoint `POST /api/auth/google` et toute la vérification de jeton Google
  côté serveur (`google-auth`).
- `frontend/js/config.js` (placeholder d'identifiant client OAuth).
- Bouton « Se connecter avec Google » et l'affichage de la photo de profil
  dans la barre de navigation.
- Dépendance `google-auth` retirée de `backend/requirements.txt`.

## [1.1.0] — 2026-08-16

### Ajouté
- Authentification via **Google Sign-In** uniquement (Google Identity
  Services côté client + vérification du jeton `id_token` côté serveur).
- Création de compte automatique à la première connexion Google (nom, email,
  photo de profil récupérés du jeton).
- `frontend/js/config.js` pour l'identifiant client OAuth, avec message
  d'avertissement clair si non configuré.
- Champ `picture` affiché dans la barre de navigation une fois connecté.

### Supprimé
- Formulaires d'inscription/connexion par email + mot de passe et la page
  `register.html`.

*(Cette version a été annulée juste après par la 1.1.1 ci-dessus.)*

## [1.0.0] — 2026-08-15

### Ajouté — version initiale (Phase 1, monolithe)
- **Backend** Flask + stockage JSON (`backend/app.py`, `backend/data/*.json`) :
  inscription/connexion par email + mot de passe, token signé façon JWT
  (HMAC), CRUD sur les lieux, recherche/filtres, recommandations
  personnalisées (préférences + popularité), favoris, itinéraires
  (création/édition/suppression/partage par lien), avis notés.
- **20 lieux réels de Yaoundé** couvrant 11 catégories : musées, monuments,
  marchés, lieux de culte, écoles, hôpitaux, bibliothèque, parcs/nature,
  restaurants, hôtels, quartiers.
- **Frontend** HTML/CSS/JS vanilla, servi par le même serveur Flask :
  - `index.html` — accueil, recommandations, catégories
  - `explore.html` — recherche, filtres, carte, grille de résultats
  - `place.html` — fiche lieu, avis, favoris, ajout au voyage, itinéraire
    routier depuis la position du visiteur
  - `trip.html` — planificateur de voyage avec budget estimé en FCFA et
    lien de partage
  - `login.html` / `register.html` — authentification classique
- **Carte** MapLibre GL JS sur tuiles vectorielles OpenStreetMap
  (OpenFreeMap `liberty`), inclinée pour un rendu proche de la 3D, avec
  extrusion des bâtiments quand le style l'expose.
- **Itinéraire routier** calculé en direct via le serveur public **OSRM**
  entre la position géolocalisée du visiteur et le lieu choisi (distance +
  durée affichées).
- **Design** : thèmes clair « Sable » et sombre « Nuit » (sélecteur dans la
  nav), palette inspirée du drapeau camerounais (vert/jaune/rouge),
  typographie Fraunces + Inter, motif signature « sept collines ».
- **Images** des lieux chargées depuis le réseau (service photographique
  seedé par lieu, pour un rendu stable dans le temps).
- `README.md` avec instructions d'installation et de lancement.
