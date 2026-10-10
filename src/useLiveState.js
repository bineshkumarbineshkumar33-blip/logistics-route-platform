import { useEffect, useRef, useState } from "react";

// Keeps one WebSocket open to FastAPI; every server push replaces the state.
export function useLiveState() {
  const [state, setState] = useState(null);
  const [connected, setConnected] = useState(false);
  const retry = useRef(0);

  useEffect(() => {
    let ws, timer, closed = false;
    const connect = () => {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${location.host}/ws`);
      ws.onopen = () => { retry.current = 0; setConnected(true); };
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === "state") setState(msg.data);
      };
      ws.onclose = () => {
        setConnected(false);
        if (!closed) timer = setTimeout(connect, Math.min(1000 * 2 ** retry.current++, 8000));
      };
    };
    connect();
    return () => { closed = true; clearTimeout(timer); ws && ws.close(); };
  }, []);

  return { state, connected };
}

const call = (url, method = "POST", body) =>
  fetch(url, { method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });

export const api = {
  setStatus: (id, status) => call(`/api/orders/${id}/status`, "PATCH", { status }),
  addOrder: (o) => call("/api/orders", "POST", o),
  randomOrder: () => call("/api/simulate/order"),
  remove: (id) => call(`/api/orders/${id}`, "DELETE"),
  reset: () => call("/api/reset"),
};
