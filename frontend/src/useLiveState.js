
import { useEffect, useState } from "react";

const API_BASE = (
  import.meta.env.VITE_API_URL || ""
).replace(/\/+$/, "");

export function useLiveState() {
  const [state, setState] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let timer;

    const loadState = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/state`);

        if (!response.ok) {
          throw new Error(`State API error: ${response.status}`);
        }

        const data = await response.json();

        if (!cancelled) {
          setState(data);
          setConnected(true);
        }
      } catch (error) {
        if (!cancelled) {
          setConnected(false);
          console.error("Failed to load backend state:", error);
        }
      } finally {
        if (!cancelled) {
          timer = setTimeout(loadState, 3000);
        }
      }
    };

    loadState();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, []);

  return { state, connected };
}

async function call(path, method = "GET", body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    throw new Error(
      `API error: ${response.status} ${await response.text()}`
    );
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  setStatus: (id, status) =>
    call(`/api/orders/${id}/status`, "PATCH", { status }),

  addOrder: (order) => call("/api/orders", "POST", order),

  randomOrder: () => call("/api/simulate/order", "POST"),

  remove: (id) => call(`/api/orders/${id}`, "DELETE"),

  reset: () => call("/api/reset", "POST"),
};
