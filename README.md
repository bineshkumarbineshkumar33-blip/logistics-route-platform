# Route Desk - Smart Algorithmic Logistics & Route Optimization Platform

A delivery dashboard where several agents carry several parcels. The backend finds short routes with
**your own** graph algorithms (no routing API), and the map updates live when a new order arrives or a parcel is delayed.

## 1. Tools to install (once)

| Tool | Version | Check in terminal | Needed for |
|---|---|---|---|
| Python | 3.10 or newer | `python --version` (Windows) / `python3 --version` | Backend |
| Node.js (includes npm) | 18 or newer | `node --version` and `npm --version` | Frontend |
| Git (optional) | any | `git --version` | GitHub portfolio |
| Docker Desktop (optional) | any | `docker --version` | PostgreSQL + PostGIS + Redis |
| VS Code (recommended) | any | - | Editor |

PostgreSQL, PostGIS, Redis and Mapbox are **optional**. Without them the app uses SQLite, in-memory state and OpenStreetMap, so it runs out of the box.

## 2. One-time setup

Unzip, open a terminal in the project folder.

**Windows (PowerShell):** `.\scripts\setup.ps1`
(If scripts are blocked: `Set-ExecutionPolicy -Scope Process Bypass` first.)

**macOS / Linux / Git Bash:** `bash scripts/setup.sh`

This creates a Python virtual environment, installs packages, runs the 6 backend tests, and runs `npm install`.

## 3. Run it (two terminals)

Terminal 1 - backend:
```
cd backend
.venv\Scripts\activate          # Windows      (macOS/Linux: source .venv/bin/activate)
uvicorn app.main:app --reload --port 8000
```
Terminal 2 - frontend:
```
cd frontend
npm run dev
```
Open **http://localhost:5173**. API docs: **http://localhost:8000/docs**.

## 4. Verify in the terminal

With the backend running, in a third terminal (venv active, project root):
```
python scripts/check_live.py
```
Expected: six `[PASS]` lines and `ALL CHECKS PASSED`.
Unit + API tests: `cd backend && python -m pytest -v` (expects `6 passed`).

Try the optimizer directly (Git Bash / macOS / Linux):
```
curl -X POST http://localhost:8000/api/optimize-route -H "Content-Type: application/json" -d '{"locations":[{"lat":17.40,"lng":78.45},{"lat":17.50,"lng":78.35},{"lat":17.44,"lng":78.40},{"lat":17.38,"lng":78.50},{"lat":17.47,"lng":78.42}]}'
```
The reply contains `sequence`, `distance_km`, `unoptimized_km` and `saved_pct`. (On Windows you can also try it in the browser at `/docs`.)

## 5. What to click in the UI
1. Each coloured line is one agent's route; numbered pins are the visiting order.
2. Press **Delay** on a stop: the parcel turns red, drops out of the route, and all routes are recomputed instantly (WebSocket push, no reload).
3. **Random order** or **Place on map** adds a parcel and routes re-balance live. Open two browser tabs to see both update together.
4. Keep adding orders until a vehicle is full: extra parcels move to another agent, or appear under **Needs attention**.

## 6. Where each DSA topic lives

| Topic | File | What it does |
|---|---|---|
| Graph, adjacency list, MST (Kruskal + union-find) | `backend/app/algorithms.py` `RoadGraph.from_points` | Builds a connected road network |
| Dijkstra (min-heap) | `RoadGraph.dijkstra`, `distance_matrix` | Shortest distance between every pair of points |
| A* (haversine heuristic) | `RoadGraph.astar` | Shortest path used to draw the polyline |
| Travelling Salesman, exact (bitmask DP) | `held_karp_open` | Best visiting order, up to 9 stops |
| Nearest neighbour + 2-opt | `nearest_neighbor`, `two_opt` | Good order for 10+ stops |
| 0/1 Knapsack | `knapsack` | Keeps the most valuable parcels that fit a vehicle |
| Greedy assignment | `backend/app/planner.py` `assign_orders` | Nearest agent first, then overflow handling |

## 7. Folder map
```
backend/app/   algorithms.py  planner.py  main.py (REST + WebSocket)  db.py  cache.py  seed.py
backend/tests/ algorithm tests + API/WebSocket test
frontend/src/  App.jsx  useLiveState.js (WebSocket hook)  components/MapView.jsx  components/Sidebar.jsx
db/schema.sql  PostGIS table      docker-compose.yml  PostgreSQL + Redis
scripts/       setup / run / check_live.py
```

## 8. Optional upgrades
- **PostgreSQL + PostGIS + Redis:** `docker compose up -d`, then set `DATABASE_URL=postgresql+psycopg2://logistics:logistics@localhost:5432/logistics` and `REDIS_URL=redis://localhost:6379/0` before starting uvicorn. The startup line then shows `database=postgresql redis=on`.
- **Mapbox:** create `frontend/.env` with `VITE_MAPBOX_TOKEN=pk...` and restart `npm run dev`.

## 9. How to talk about it in interviews
- "I built the routing core myself: Dijkstra for the distance matrix, A* for paths, Held-Karp for exact TSP up to 9 stops and 2-opt beyond, knapsack for vehicle load."
- "Re-planning 10 parcels across 3 agents takes about 2 ms, so every change is pushed to all browsers over WebSockets."
- "The standalone `/api/optimize-route` endpoint cut a sample 5-stop route by about 46% versus visiting in input order."
- Know the complexity: Dijkstra O((V+E) log V), Held-Karp O(n^2 * 2^n), knapsack O(n * capacity).

## 10. Extend it in 4th year
Real road data from OpenStreetMap (OSMnx) instead of the synthetic graph; delivery time windows; agents that move along the route (GPS simulation in Redis); JWT login; deploy backend on Render and frontend on Vercel; Dockerfile for the whole app; GitHub Actions running the tests.
