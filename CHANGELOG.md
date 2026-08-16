# Changelog — GlobeTrotter Yaoundé (Phase 1)

Toutes les versions notables de ce projet sont documentées ici.

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
