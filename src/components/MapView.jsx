import { useEffect, useRef } from "react";
import L from "leaflet";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap, useMapEvents } from "react-leaflet";

const token = import.meta.env.VITE_MAPBOX_TOKEN;
const tiles = token
  ? { url: `https://api.mapbox.com/styles/v1/mapbox/light-v11/tiles/{z}/{x}/{y}?access_token=${token}`, tileSize: 512, zoomOffset: -1,
      attribution: "© Mapbox © OpenStreetMap" }
  : { url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", tileSize: 256, zoomOffset: 0, attribution: "© OpenStreetMap contributors" };

const pin = (cls, html = "", color) =>
  L.divIcon({ className: "", html: `<div class="${cls}" style="${color ? `background:${color}` : ""}">${html}</div>`, iconSize: [24, 24], iconAnchor: [12, 12] });

function FitOnce({ points }) {
  const map = useMap();
  const done = useRef(false);
  useEffect(() => {
    if (!done.current && points.length) {
      map.fitBounds(points, { padding: [50, 50] });
      done.current = true;
    }
  }, [points, map]);
  return null;
}

function ClickToPlace({ armed, onPlace }) {
  useMapEvents({ click: (e) => armed && onPlace(e.latlng.lat, e.latlng.lng) });
  return null;
}

export default function MapView({ state, armed, onPlace, onStatus }) {
  const { plan, depot, orders } = state;
  const lateOrders = orders.filter((o) => o.status === "delayed" || plan.unassigned.includes(o.id));
  const allPoints = [[depot.lat, depot.lng], ...orders.map((o) => [o.lat, o.lng])];

  return (
    <MapContainer center={[depot.lat, depot.lng]} zoom={12} className={`h-full w-full ${armed ? "cursor-crosshair" : ""}`} style={armed ? { cursor: "crosshair" } : undefined}>
      <TileLayer url={tiles.url} tileSize={tiles.tileSize} zoomOffset={tiles.zoomOffset} attribution={tiles.attribution} />
      <FitOnce points={allPoints} />
      <ClickToPlace armed={armed} onPlace={onPlace} />

      <Marker position={[depot.lat, depot.lng]} icon={pin("hub-pin")}><Popup>{depot.name}</Popup></Marker>

      {plan.routes.map((r) => (
        <div key={r.agent_id}>
          <Polyline positions={r.path} pathOptions={{ color: r.color, weight: 5, opacity: 0.85 }} />
          <Marker position={r.start} icon={pin("agent-pin", "", r.color)}><Popup>{r.name} starts here</Popup></Marker>
          {r.stops.map((s) => (
            <Marker key={s.order_id} position={[s.lat, s.lng]} icon={pin("stop-pin", s.seq, r.color)}>
              <Popup>
                <b>{s.name}</b><br />{r.name} · stop {s.seq} · arrives in {Math.round(s.eta_min)} min<br />{s.weight_kg} kg
                <div className="mt-2"><button className="rounded bg-late px-2 py-1 text-white" onClick={() => onStatus(s.order_id, "delayed")}>Mark delayed</button></div>
              </Popup>
            </Marker>
          ))}
        </div>
      ))}

      {lateOrders.map((o) => (
        <Marker key={o.id} position={[o.lat, o.lng]} icon={pin("stop-pin late-pin", "!")}>
          <Popup>
            <b>{o.name}</b><br />{o.status === "delayed" ? "Delayed, removed from routes" : "No vehicle has room"}
            {o.status === "delayed" && (
              <div className="mt-2"><button className="rounded bg-ink px-2 py-1 text-white" onClick={() => onStatus(o.id, "pending")}>Put back on route</button></div>
            )}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
