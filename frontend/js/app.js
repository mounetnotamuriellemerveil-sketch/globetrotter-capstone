/* ==========================================================================
   GlobeTrotter Yaoundé — shared app shell
   Handles: theme switch (Sable/Nuit), nav/footer injection, auth state,
   toast notifications, tiny fetch wrapper with Bearer token.
   ========================================================================== */

const API_BASE = ""; // same-origin, Flask serves both API and frontend

const Store = {
  getToken: () => localStorage.getItem("gt_token"),
  setToken: (t) => localStorage.setItem("gt_token", t),
  clearToken: () => localStorage.removeItem("gt_token"),
  getUser: () => JSON.parse(localStorage.getItem("gt_user") || "null"),
  setUser: (u) => localStorage.setItem("gt_user", JSON.stringify(u)),
  clearUser: () => localStorage.removeItem("gt_user"),
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
  const saved = localStorage.getItem("gt_theme") || "sable";
  applyTheme(saved);
}
function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "sable";
  applyTheme(current === "sable" ? "nuit" : "sable");
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
    ["index.html", "Accueil"],
    ["explore.html", "Explorer"],
    ["trip.html", "Mon voyage"],
  ];

  root.innerHTML = `
    <nav class="topnav">
      <div class="container">
        <a href="index.html" class="brand">${LOGO_MARK}<span>GlobeTrotter<br><small>Sept Collines · Yaoundé</small></span></a>
        <div class="nav-links">
          ${links.map(([href, label]) => `<a href="${href}" class="${path === href ? "active" : ""}">${label}</a>`).join("")}
        </div>
        <div class="nav-actions">
          <button id="theme-toggle" class="icon-btn" title="Changer de thème">🌙</button>
          ${user
            ? `<span class="hint" style="font-weight:600;font-size:.85rem;margin-right:2px;">${user.name.split(" ")[0]}</span>
               <button id="logout-btn" class="btn btn-ghost btn-sm">Déconnexion</button>`
            : `<a href="login.html" class="btn btn-ghost btn-sm">Connexion</a>
               <a href="register.html" class="btn btn-primary btn-sm">Créer un compte</a>`
          }
        </div>
      </div>
    </nav>`;

  document.getElementById("theme-toggle").addEventListener("click", toggleTheme);
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      Store.clearToken();
      Store.clearUser();
      toast("Vous êtes déconnecté(e)");
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
            <p style="max-width:38ch;">Un compagnon de voyage pensé pour découvrir la ville aux sept collines : lieux, itinéraires et budget, tout au même endroit.</p>
          </div>
          <div>
            <h5>Explorer</h5>
            <a href="explore.html">Tous les lieux</a>
            <a href="explore.html?category=restaurant">Restaurants</a>
            <a href="explore.html?category=parc">Nature &amp; parcs</a>
            <a href="explore.html?category=hotel">Hôtels</a>
          </div>
          <div>
            <h5>Compte</h5>
            <a href="trip.html">Mon voyage</a>
            <a href="login.html">Connexion</a>
            <a href="register.html">Créer un compte</a>
          </div>
        </div>
        <div class="foot-bottom">
          <span>© 2026 GlobeTrotter Yaoundé — Phase 1, projet Systèmes Distribués (CS 4122)</span>
          <span>Fond de carte © contributeurs OpenStreetMap</span>
        </div>
      </div>
    </footer>`;
}

/* ---------------- category label/icon helpers ---------------- */
const CATEGORY_META = {
  musee: { label: "Musée", icon: "🏛️" },
  monument: { label: "Monument", icon: "🗿" },
  marche: { label: "Marché", icon: "🧺" },
  religieux: { label: "Lieu de culte", icon: "⛪" },
  ecole: { label: "Éducation", icon: "🎓" },
  hopital: { label: "Santé", icon: "🏥" },
  bibliotheque: { label: "Bibliothèque", icon: "📚" },
  parc: { label: "Nature", icon: "🌳" },
  restaurant: { label: "Restaurant", icon: "🍽️" },
  hotel: { label: "Hôtel", icon: "🛏️" },
  quartier: { label: "Quartier", icon: "📍" },
};
function categoryMeta(cat) {
  return CATEGORY_META[cat] || { label: cat, icon: "📍" };
}
function priceDots(level) {
  let out = "";
  for (let i = 0; i < 4; i++) out += `<span class="${i < level ? "on" : ""}">FCFA</span>`;
  return level === 0
    ? '<span style="font-size:.78rem;color:var(--green);font-weight:700;">Gratuit</span>'
    : `<span class="price-dots" style="font-size:.72rem;">${"●".repeat(level)}${"○".repeat(4 - level)}</span>`;
}
function placeImage(place, w = 640, h = 440) {
  // Stable network-served imagery keyed to each place (Picsum's seeded API
  // guarantees the same photo every time, unlike hot-linked Wikimedia URLs
  // which break when pages are edited).
  return `https://picsum.photos/seed/${encodeURIComponent(place.image_seed)}/${w}/${h}`;
}
function stars(rating) {
  const full = Math.round(rating);
  return "★".repeat(full) + "☆".repeat(5 - full);
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  renderNav();
  renderFooter();
});
