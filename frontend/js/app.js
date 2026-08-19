/* ==========================================================================
   GlobeTrotter Yaoundé — shared app shell (Phase 2)
   Handles: theme switch (Sable/Nuit), language switch (FR/EN), nav/footer
   injection, auth state, toast, fetch helper, and live network place photos
   (Wikipedia, with a stable fallback if a page has no usable image).
   ========================================================================== */

const API_BASE = ""; // same-origin — the API Gateway proxies /api/* for us

const Store = {
  getToken: () => localStorage.getItem("gt_token"),
  setToken: (t) => localStorage.setItem("gt_token", t),
  clearToken: () => localStorage.removeItem("gt_token"),
  getUser: () => JSON.parse(localStorage.getItem("gt_user") || "null"),
  setUser: (u) => localStorage.setItem("gt_user", JSON.stringify(u)),
  clearUser: () => localStorage.removeItem("gt_user"),
  getLang: () => localStorage.getItem("gt_lang") || "fr",
  setLang: (l) => localStorage.setItem("gt_lang", l),
};

async function api(path, options = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
  const token = Store.getToken();
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(API_BASE + path, Object.assign({}, options, { headers }));
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Une erreur est survenue");
  return data;
}

function toast(message) {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove("show"), 2600);
}

/* ---------------- theme ---------------- */
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("gt_theme", theme);
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = theme === "nuit" ? "☀️" : "🌙";
}
function initTheme() {
  applyTheme(localStorage.getItem("gt_theme") || "sable");
}
function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "sable";
  applyTheme(current === "sable" ? "nuit" : "sable");
}

/* ---------------- language (FR/EN) ---------------- */
const I18N = {
  fr: {
    nav_home: "Accueil", nav_explore: "Explorer", nav_trip: "Mon voyage",
    nav_login: "Connexion", nav_register: "Créer un compte", nav_logout: "Déconnexion",
    hero_badge: "Phase 2 · Architecture microservices",
    hero_title_pre: "Planifiez votre passage à ", hero_title_em: "Yaoundé", hero_title_post: ", la ville aux sept collines.",
    hero_lede: "Découvrez 30 lieux incontournables, obtenez un itinéraire jusqu'à votre destination sur une carte OpenStreetMap, et construisez votre voyage avec un budget estimé en francs CFA.",
    hero_cta_explore: "Explorer les lieux", hero_cta_trip: "Créer mon itinéraire",
    stat_places: "Lieux référencés", stat_categories: "Catégories", stat_hills: "Collines mythiques",
    reco_kicker: "Recommandé pour vous", reco_title: "Les lieux les mieux notés en ce moment", see_all: "Voir tout →",
    cat_kicker: "Par catégorie", cat_title: "Que cherchez-vous à Yaoundé ?",
    explore_kicker: "30 lieux à Yaoundé", explore_title: "Explorer la ville",
    map_hint: "Carte 3D — clic-glissez pour incliner, molette pour zoomer.",
    search_label: "Recherche", search_ph: "Un lieu, un quartier...",
    filter_category: "Catégorie", filter_budget: "Budget maximum",
    budget_all: "Tous budgets", budget_free: "Gratuit uniquement",
    see_more: "Voir →", free: "Gratuit",
    fav_add: "Ajouter aux favoris", trip_add: "+ Ajouter au voyage",
    reviews_title: "Avis des voyageurs", no_reviews: "Aucun avis pour le moment. Soyez le premier à partager votre expérience.",
    route_title: "Itinéraire depuis votre position", route_hint: "Autorisez la géolocalisation pour tracer le trajet routier jusqu'à ce lieu (données OpenStreetMap / OSRM).",
    route_btn: "📍 Me guider jusqu'ici",
    footer_tagline: "Un compagnon de voyage pensé pour découvrir la ville aux sept collines : lieux, itinéraires et budget, tout au même endroit.",
    footer_explore: "Explorer", footer_all_places: "Tous les lieux", footer_restaurants: "Restaurants", footer_nature: "Nature & parcs", footer_hotels: "Hôtels",
    footer_account: "Compte", footer_bottom: "Fond de carte © contributeurs OpenStreetMap",
    trip_kicker: "Planificateur", trip_title: "Mon voyage à Yaoundé",
    trip_new: "Nouvel itinéraire", trip_name: "Nom du voyage", trip_name_ph: "Ex : Week-end à Yaoundé",
    trip_start: "Arrivée", trip_end: "Départ", trip_places: "Lieux à visiter", trip_selected: "sélectionné(s)",
    trip_create: "Créer l'itinéraire", trip_yours: "Vos itinéraires", trip_none: "Aucun itinéraire pour l'instant.",
    trip_share: "🔗 Partager", trip_delete: "Supprimer", trip_dates_tbd: "Dates à définir",
    gate_msg: "Connectez-vous pour créer et sauvegarder votre itinéraire.",
  },
  en: {
    nav_home: "Home", nav_explore: "Explore", nav_trip: "My trip",
    nav_login: "Log in", nav_register: "Sign up", nav_logout: "Log out",
    hero_badge: "Phase 2 · Microservices architecture",
    hero_title_pre: "Plan your visit to ", hero_title_em: "Yaoundé", hero_title_post: ", the city of seven hills.",
    hero_lede: "Discover 30 must-see places, get a route to your destination on an OpenStreetMap map, and build your trip with a budget estimate in CFA francs.",
    hero_cta_explore: "Explore places", hero_cta_trip: "Plan my trip",
    stat_places: "Places listed", stat_categories: "Categories", stat_hills: "Legendary hills",
    reco_kicker: "Recommended for you", reco_title: "Top-rated places right now", see_all: "See all →",
    cat_kicker: "By category", cat_title: "What are you looking for in Yaoundé?",
    explore_kicker: "30 places in Yaoundé", explore_title: "Explore the city",
    map_hint: "3D map — drag to tilt, scroll to zoom.",
    search_label: "Search", search_ph: "A place, a neighbourhood...",
    filter_category: "Category", filter_budget: "Maximum budget",
    budget_all: "All budgets", budget_free: "Free only",
    see_more: "See →", free: "Free",
    fav_add: "Add to favorites", trip_add: "+ Add to trip",
    reviews_title: "Traveler reviews", no_reviews: "No reviews yet. Be the first to share your experience.",
    route_title: "Directions from your location", route_hint: "Allow geolocation to draw a driving route to this place (OpenStreetMap / OSRM data).",
    route_btn: "📍 Guide me there",
    footer_tagline: "A travel companion built to explore the city of seven hills: places, itineraries and budget, all in one place.",
    footer_explore: "Explore", footer_all_places: "All places", footer_restaurants: "Restaurants", footer_nature: "Nature & parks", footer_hotels: "Hotels",
    footer_account: "Account", footer_bottom: "Map data © OpenStreetMap contributors",
    trip_kicker: "Planner", trip_title: "My trip to Yaoundé",
    trip_new: "New itinerary", trip_name: "Trip name", trip_name_ph: "e.g. Weekend in Yaoundé",
    trip_start: "Arrival", trip_end: "Departure", trip_places: "Places to visit", trip_selected: "selected",
    trip_create: "Create itinerary", trip_yours: "Your itineraries", trip_none: "No itinerary yet.",
    trip_share: "🔗 Share", trip_delete: "Delete", trip_dates_tbd: "Dates to be set",
    gate_msg: "Log in to create and save your itinerary.",
  },
};
function t(key) {
  const lang = Store.getLang();
  return (I18N[lang] && I18N[lang][key]) || (I18N.fr[key]) || key;
}
function applyStaticI18n(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((el) => (el.textContent = t(el.dataset.i18n)));
  root.querySelectorAll("[data-i18n-ph]").forEach((el) => (el.placeholder = t(el.dataset.i18nPh)));
  const langBtn = document.getElementById("lang-toggle");
  if (langBtn) langBtn.textContent = Store.getLang().toUpperCase();
}
function toggleLang() {
  Store.setLang(Store.getLang() === "fr" ? "en" : "fr");
  location.reload();
}
function placeText(p, field) {
  // e.g. placeText(p, "description") -> p.description_en when lang=en and present
  const lang = Store.getLang();
  if (lang === "en" && p[field + "_en"]) return p[field + "_en"];
  return p[field];
}

/* ---------------- hill-ridge signature svg (7 hills of Yaoundé) --------- */
const HILL_RIDGE_SVG = `
<svg class="hill-ridge" viewBox="0 0 700 40" preserveAspectRatio="none" aria-hidden="true">
  <path opacity="0.35" d="M0,40 L0,26 Q40,6 80,22 T160,20 T240,10 T320,24 T400,14 T480,26 T560,16 T640,24 T700,18 L700,40 Z"/>
  <path opacity="0.6" d="M0,40 L0,32 Q60,16 120,30 T240,26 T360,18 T480,30 T600,22 T700,28 L700,40 Z"/>
  <path d="M0,40 L0,36 Q90,24 180,34 T350,30 T520,34 T700,32 L700,40 Z"/>
</svg>`;

const LOGO_MARK = `
<svg class="mark" viewBox="0 0 32 32" aria-hidden="true">
  <circle cx="16" cy="16" r="16" fill="#0B6E4F"/>
  <path d="M2,22 Q8,14 14,20 T26,16 L26,26 Q16,29 6,26 Z" fill="#FDB913"/>
  <path d="M0,26 Q10,20 16,25 T32,22 L32,32 L0,32 Z" fill="#D7263D" opacity="0.85"/>
</svg>`;

/* ---------------- nav + footer ---------------- */
function renderNav() {
  const root = document.getElementById("nav-root");
  if (!root) return;
  const user = Store.getUser();
  const path = location.pathname.split("/").pop() || "index.html";

  const links = [
    ["index.html", t("nav_home")],
    ["explore.html", t("nav_explore")],
    ["trip.html", t("nav_trip")],
  ];

  root.innerHTML = `
    <nav class="topnav">
      <div class="container">
        <a href="index.html" class="brand">${LOGO_MARK}<span>GlobeTrotter<br><small>Sept Collines · Yaoundé</small></span></a>
        <div class="nav-links">
          ${links.map(([href, label]) => `<a href="${href}" class="${path === href ? "active" : ""}">${label}</a>`).join("")}
        </div>
        <div class="nav-actions">
          <button id="lang-toggle" class="icon-btn" title="Change language / Changer de langue" style="font-size:.72rem;font-weight:800;">${Store.getLang().toUpperCase()}</button>
          <button id="theme-toggle" class="icon-btn" title="Changer de thème">🌙</button>
          ${user
            ? `<span class="hint" style="font-weight:600;font-size:.85rem;margin-right:2px;">${user.name.split(" ")[0]}</span>
               <button id="logout-btn" class="btn btn-ghost btn-sm">${t("nav_logout")}</button>`
            : `<a href="login.html" class="btn btn-ghost btn-sm">${t("nav_login")}</a>
               <a href="register.html" class="btn btn-primary btn-sm">${t("nav_register")}</a>`
          }
        </div>
      </div>
    </nav>`;

  document.getElementById("theme-toggle").addEventListener("click", toggleTheme);
  document.getElementById("lang-toggle").addEventListener("click", toggleLang);
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      Store.clearToken();
      Store.clearUser();
      toast(Store.getLang() === "en" ? "You are logged out" : "Vous êtes déconnecté(e)");
      setTimeout(() => (location.href = "index.html"), 500);
    });
  }
  initTheme();
}

function renderFooter() {
  const root = document.getElementById("footer-root");
  if (!root) return;
  root.innerHTML = `
    <footer>
      <div class="container">
        ${HILL_RIDGE_SVG}
        <div class="foot-grid">
          <div>
            <a href="index.html" class="brand" style="margin-bottom:10px;">${LOGO_MARK}<span>GlobeTrotter Yaoundé</span></a>
            <p style="max-width:38ch;">${t("footer_tagline")}</p>
          </div>
          <div>
            <h5>${t("footer_explore")}</h5>
            <a href="explore.html">${t("footer_all_places")}</a>
            <a href="explore.html?category=restaurant">${t("footer_restaurants")}</a>
            <a href="explore.html?category=parc">${t("footer_nature")}</a>
            <a href="explore.html?category=hotel">${t("footer_hotels")}</a>
          </div>
          <div>
            <h5>${t("footer_account")}</h5>
            <a href="trip.html">${t("nav_trip")}</a>
            <a href="login.html">${t("nav_login")}</a>
            <a href="register.html">${t("nav_register")}</a>
          </div>
        </div>
        <div class="foot-bottom">
          <span>© 2026 GlobeTrotter Yaoundé — Phase 2, projet Systèmes Distribués (CS 4122)</span>
          <span>${t("footer_bottom")}</span>
        </div>
      </div>
    </footer>`;
}

/* ---------------- category label/icon helpers ---------------- */
const CATEGORY_META = {
  musee: { label: "Musée", label_en: "Museum", icon: "🏛️" },
  monument: { label: "Monument", label_en: "Monument", icon: "🗿" },
  marche: { label: "Marché", label_en: "Market", icon: "🧺" },
  religieux: { label: "Lieu de culte", label_en: "Place of worship", icon: "⛪" },
  ecole: { label: "Éducation", label_en: "Education", icon: "🎓" },
  hopital: { label: "Santé", label_en: "Health", icon: "🏥" },
  bibliotheque: { label: "Bibliothèque", label_en: "Library", icon: "📚" },
  parc: { label: "Nature", label_en: "Nature", icon: "🌳" },
  restaurant: { label: "Restaurant", label_en: "Restaurant", icon: "🍽️" },
  hotel: { label: "Hôtel", label_en: "Hotel", icon: "🛏️" },
  quartier: { label: "Quartier", label_en: "Neighbourhood", icon: "📍" },
  sport: { label: "Sport", label_en: "Sport", icon: "🏟️" },
  transport: { label: "Transport", label_en: "Transport", icon: "🚉" },
  shopping: { label: "Shopping", label_en: "Shopping", icon: "🛍️" },
  cinema: { label: "Cinéma", label_en: "Cinema", icon: "🎬" },
  culture: { label: "Culture", label_en: "Culture", icon: "🎭" },
};
function categoryMeta(cat) {
  const meta = CATEGORY_META[cat] || { label: cat, label_en: cat, icon: "📍" };
  return { icon: meta.icon, label: Store.getLang() === "en" ? meta.label_en : meta.label };
}
function priceDots(level) {
  if (level === 0) return `<span style="font-size:.78rem;color:var(--green);font-weight:700;">${t("free")}</span>`;
  return `<span class="price-dots" style="font-size:.72rem;">${"●".repeat(level)}${"○".repeat(4 - level)}</span>`;
}
function stars(rating) {
  const full = Math.round(rating);
  return "★".repeat(full) + "☆".repeat(5 - full);
}

/* ---------------- images: live network photos with graceful fallback --- */
function placeImage(place, w = 640, h = 440) {
  // Instant, stable placeholder shown immediately; hydrateImages() swaps
  // this for a real photo of the place fetched from Wikipedia when available.
  return `https://picsum.photos/seed/${encodeURIComponent(place.image_seed)}/${w}/${h}`;
}
function placeImgTag(place, w = 640, h = 440, cls = "") {
  const query = encodeURIComponent(place.image_query || `${place.name} Yaoundé`);
  return `<img class="${cls}" data-query="${query}" data-seed="${place.image_seed}" data-w="${w}" src="${placeImage(place, w, h)}" alt="${place.name}" loading="lazy">`;
}
async function fetchWikiImage(query, width) {
  const cacheKey = "gt_wimg_" + query + "_" + width;
  const cached = sessionStorage.getItem(cacheKey);
  if (cached) return cached;
  try {
    const url = `https://fr.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch=${encodeURIComponent(query)}&gsrlimit=1&prop=pageimages&piprop=thumbnail&pithumbsize=${width}&format=json&origin=*`;
    const res = await fetch(url);
    const data = await res.json();
    const pages = data.query && data.query.pages;
    if (pages) {
      const page = Object.values(pages)[0];
      const src = page && page.thumbnail && page.thumbnail.source;
      if (src) {
        sessionStorage.setItem(cacheKey, src);
        return src;
      }
    }
  } catch (e) { /* network hiccup — keep the placeholder */ }
  return null;
}
function hydrateImages(root = document) {
  root.querySelectorAll("img[data-query]").forEach(async (img) => {
    const query = decodeURIComponent(img.dataset.query);
    const width = Number(img.dataset.w) || 640;
    const real = await fetchWikiImage(query, width);
    if (real) img.src = real;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  renderNav();
  renderFooter();
  applyStaticI18n();
});
