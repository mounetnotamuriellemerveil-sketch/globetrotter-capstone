/* ==========================================================================
   GlobeTrotter Yaoundé — map helpers
   MapLibre GL JS rendering OpenStreetMap vector tiles (OpenFreeMap "liberty"
   style, no API key needed) tilted for a 3D-building look, plus OSRM for
   real routes from the visitor's location to a place.
   ========================================================================== */

const OSM_STYLE = "https://tiles.openfreemap.org/styles/liberty";
const YAOUNDE_CENTER = [11.5167, 3.8667];

function makeMap(containerId, { center = YAOUNDE_CENTER, zoom = 12.5, pitch = 55, bearing = -12 } = {}) {
  const map = new maplibregl.Map({
    container: containerId,
    style: OSM_STYLE,
    center,
    zoom,
    pitch,
    bearing,
    antialias: true,
  });
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");

  map.on("load", () => {
    // gentle 3D building extrusion if the style/source exposes it
    const layers = map.getStyle().layers || [];
    const buildingLayer = layers.find((l) => l.id && /building/i.test(l.id) && l.type === "fill");
    if (buildingLayer) {
      try {
        map.setPaintProperty(buildingLayer.id, "fill-extrusion-height", ["get", "render_height"]);
      } catch (e) {
        /* style may not support extrusion — safe to ignore */
      }
    }
  });
  return map;
}

function pinMarker(color = "#0B6E4F") {
  const el = document.createElement("div");
  el.style.width = "26px";
  el.style.height = "26px";
  el.style.borderRadius = "50% 50% 50% 0";
  el.style.transform = "rotate(-45deg)";
  el.style.background = color;
  el.style.border = "2px solid white";
  el.style.boxShadow = "0 4px 10px rgba(0,0,0,.35)";
  return el;
}

function addPlaceMarkers(map, places, { onSelect } = {}) {
  const bounds = new maplibregl.LngLatBounds();
  places.forEach((p) => {
    const meta = categoryMeta(p.category);
    const marker = new maplibregl.Marker({ element: pinMarker("#0B6E4F") })
      .setLngLat([p.lng, p.lat])
      .setPopup(
        new maplibregl.Popup({ offset: 20 }).setHTML(
          `<h4>${meta.icon} ${p.name}</h4><p style="margin:0;font-size:.82rem;">${p.quartier}</p>`
        )
      )
      .addTo(map);
    if (onSelect) marker.getElement().addEventListener("click", () => onSelect(p));
    bounds.extend([p.lng, p.lat]);
  });
  if (places.length) map.fitBounds(bounds, { padding: 60, maxZoom: 14, duration: 0 });
}

function getVisitorLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve([pos.coords.longitude, pos.coords.latitude]),
      () => resolve(null),
      { timeout: 6000 }
    );
  });
}

/** Draws a route from `from` [lng,lat] to `to` [lng,lat] on `map` using OSRM's
 *  free public routing server (driving profile). Returns distance/duration. */
async function drawRoute(map, from, to, sourceId = "gt-route") {
  const url = `https://router.project-osrm.org/route/v1/driving/${from[0]},${from[1]};${to[0]},${to[1]}?overview=full&geometries=geojson`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Itinéraire indisponible pour le moment");
  const data = await res.json();
  const route = data.routes && data.routes[0];
  if (!route) throw new Error("Aucun itinéraire trouvé");

  const geojson = { type: "Feature", geometry: route.geometry, properties: {} };

  if (map.getSource(sourceId)) {
    map.getSource(sourceId).setData(geojson);
  } else {
    map.addSource(sourceId, { type: "geojson", data: geojson });
    map.addLayer({
      id: sourceId + "-casing",
      type: "line",
      source: sourceId,
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": "#ffffff", "line-width": 9, "line-opacity": 0.9 },
    });
    map.addLayer({
      id: sourceId + "-line",
      type: "line",
      source: sourceId,
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": "#D7263D", "line-width": 5 },
    });
  }

  new maplibregl.Marker({ element: pinMarker("#1C1B17") }).setLngLat(from).addTo(map);

  const bounds = route.geometry.coordinates.reduce(
    (b, c) => b.extend(c),
    new maplibregl.LngLatBounds(route.geometry.coordinates[0], route.geometry.coordinates[0])
  );
  map.fitBounds(bounds, { padding: 70, duration: 800 });

  return { distanceKm: route.distance / 1000, durationMin: route.duration / 60 };
}
