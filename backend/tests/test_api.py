from fastapi.testclient import TestClient

from app.main import app


def test_full_flow():
    with TestClient(app) as c:
        assert c.get("/api/health").json()["status"] == "ok"
        state = c.get("/api/state").json()
        assert len(state["plan"]["routes"]) == 3

        # Step 2 endpoint: optimise a custom list (works with and without trailing slash)
        body = {"locations": [{"lat": 17.40, "lng": 78.45}, {"lat": 17.50, "lng": 78.35},
                              {"lat": 17.44, "lng": 78.40}, {"lat": 17.38, "lng": 78.50},
                              {"lat": 17.47, "lng": 78.42}]}
        for url in ("/api/optimize-route", "/api/optimize-route/"):
            r = c.post(url, json=body, follow_redirects=True).json()
            assert sorted(r["sequence"]) == [0, 1, 2, 3, 4] and r["distance_km"] <= r["unoptimized_km"]

        # Step 4: websocket gets pushed an update when an order is delayed
        with c.websocket_connect("/ws") as ws:
            assert ws.receive_json()["type"] == "state"
            before = c.get("/api/state").json()["version"]
            assert c.patch("/api/orders/1/status", json={"status": "delayed"}).status_code == 200
            msg = ws.receive_json()
            assert msg["data"]["version"] > before
            routed = {s["order_id"] for rt in msg["data"]["plan"]["routes"] for s in rt["stops"]}
            assert 1 not in routed

        # dynamic re-routing on a new order
        n_before = sum(len(r["stops"]) for r in c.get("/api/state").json()["plan"]["routes"])
        c.post("/api/orders", json={"name": "Test", "lat": 17.42, "lng": 78.40, "weight_kg": 2})
        n_after = sum(len(r["stops"]) for r in c.get("/api/state").json()["plan"]["routes"])
        assert n_after == n_before + 1
        assert c.post("/api/reset").status_code == 200
