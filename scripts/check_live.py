"""Terminal smoke test against a RUNNING backend (http://localhost:8000).
Run:  python scripts/check_live.py"""
import json
import sys

import httpx
from websockets.sync.client import connect

BASE = "http://localhost:8000"
ok = True


def check(label, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(f"[{'PASS' if cond else 'FAIL'}] {label} {extra}")


try:
    c = httpx.Client(base_url=BASE, timeout=10)
    h = c.get("/api/health").json()
    check("health endpoint", h["status"] == "ok", f"(database={h['database']}, redis={h['redis']})")

    r = c.post("/api/reset").json()
    check("demo data loaded: 3 routes", len(r["plan"]["routes"]) == 3,
          f"total {r['plan']['total_distance_km']} km in {r['plan']['compute_ms']} ms")

    body = {"locations": [{"lat": 17.40, "lng": 78.45}, {"lat": 17.50, "lng": 78.35}, {"lat": 17.44, "lng": 78.40},
                          {"lat": 17.38, "lng": 78.50}, {"lat": 17.47, "lng": 78.42}]}
    o = c.post("/api/optimize-route", json=body).json()
    check("optimize-route (5 stops)", sorted(o["sequence"]) == [0, 1, 2, 3, 4],
          f"order={o['sequence']} {o['distance_km']} km vs {o['unoptimized_km']} km unoptimized, saved {o['saved_pct']}%")

    with connect("ws://localhost:8000/ws") as ws:
        first = json.loads(ws.recv())
        check("websocket sends initial state", first["type"] == "state")
        c.patch("/api/orders/3/status", json={"status": "delayed"})
        msg = json.loads(ws.recv())
        routed = {s["order_id"] for rt in msg["data"]["plan"]["routes"] for s in rt["stops"]}
        check("delayed order pushed live and removed from routes", 3 not in routed,
              f"(state v{msg['data']['version']})")
        c.post("/api/orders", json={"name": "Check order", "lat": 17.42, "lng": 78.41, "weight_kg": 2})
        msg = json.loads(ws.recv())
        check("new order triggers live re-route", any(s["name"] == "Check order"
              for rt in msg["data"]["plan"]["routes"] for s in rt["stops"]))
    c.post("/api/reset")
except Exception as e:
    print(f"[FAIL] could not complete checks: {e}\nIs the backend running?  (see README step 3)")
    sys.exit(1)

print("\nALL CHECKS PASSED" if ok else "\nSOME CHECKS FAILED")
sys.exit(0 if ok else 1)
