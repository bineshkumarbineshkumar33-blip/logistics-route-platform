"""Turns agents + orders into per-agent routes using the algorithms module."""
from __future__ import annotations

import math
import time
from typing import Dict, List

from .algorithms import RoadGraph, distance_matrix, knapsack, route_cost, solve_open_tsp

SPEED_KMPH = 28.0      # average city speed
SERVICE_MIN = 4.0      # minutes spent at each drop


def _wt(order: dict) -> int:
    return max(1, math.ceil(order["weight_kg"]))


def assign_orders(agents: List[dict], orders: List[dict], d):
    """Phase 1: each order goes to its nearest agent (greedy).
    Phase 2: if an agent is over capacity, a 0/1 knapsack keeps the most valuable
             parcels (priority-weighted); the rest are re-offered to agents with room."""
    assigned: Dict[int, List[dict]] = {a["id"]: [] for a in agents}
    if not agents:
        return assigned, list(orders)

    def key(a, o):
        return d[(f"A:{a['id']}", f"O:{o['id']}")]

    buckets: Dict[int, List[dict]] = {a["id"]: [] for a in agents}
    for o in sorted(orders, key=lambda o: (-o["priority"], o["id"])):
        buckets[min(agents, key=lambda a: key(a, o))["id"]].append(o)

    leftover: List[dict] = []
    for a in agents:
        mine = buckets[a["id"]]
        items = [(o["id"], _wt(o), o["priority"] * 100 + 1) for o in mine]
        chosen, _ = knapsack(items, int(a["capacity_kg"]))
        assigned[a["id"]] = [o for o in mine if o["id"] in chosen]
        leftover += [o for o in mine if o["id"] not in chosen]

    unassigned: List[dict] = []
    for o in sorted(leftover, key=lambda o: -o["priority"]):
        fits = [a for a in agents if sum(_wt(x) for x in assigned[a["id"]]) + _wt(o) <= a["capacity_kg"]]
        if not fits:
            unassigned.append(o)
            continue
        best = min(fits, key=lambda a: min([key(a, o)] + [d[(f"O:{x['id']}", f"O:{o['id']}")] for x in assigned[a["id"]]]))
        assigned[best["id"]].append(o)
    return assigned, unassigned


def plan_routes(agents: List[dict], orders: List[dict]) -> dict:
    t0 = time.perf_counter()
    active = [o for o in orders if o["status"] == "pending"]
    points = {f"A:{a['id']}": (a["lat"], a["lng"]) for a in agents}
    points.update({f"O:{o['id']}": (o["lat"], o["lng"]) for o in active})
    if not points:
        return {"routes": [], "unassigned": [], "total_distance_km": 0.0, "compute_ms": 0.0}

    graph = RoadGraph.from_points(points, k=3)
    d = distance_matrix(graph, list(points))
    assigned, unassigned = assign_orders(agents, active, d)
    by_id = {o["id"]: o for o in active}

    routes, total = [], 0.0
    for a in agents:
        start = f"A:{a['id']}"
        stops_ids = [f"O:{o['id']}" for o in assigned[a["id"]]]
        order, km, algo = solve_open_tsp(start, stops_ids, d)

        path = [list(graph.coords[start])]
        stops, cum = [], 0.0
        cur = start
        for i, node in enumerate(order, 1):
            seg_km, seg_nodes = graph.shortest_path(cur, node)   # A* for the drawn polyline
            path += [list(graph.coords[n]) for n in seg_nodes[1:]]
            cum += seg_km
            o = by_id[int(node.split(":")[1])]
            stops.append({
                "seq": i, "order_id": o["id"], "name": o["name"], "lat": o["lat"], "lng": o["lng"],
                "priority": o["priority"], "weight_kg": o["weight_kg"],
                "eta_min": round(cum / SPEED_KMPH * 60 + SERVICE_MIN * (i - 1), 1),
            })
            cur = node
        total += km
        routes.append({
            "agent_id": a["id"], "name": a["name"], "color": a["color"],
            "start": [a["lat"], a["lng"]], "capacity_kg": a["capacity_kg"],
            "load_kg": sum(s["weight_kg"] for s in stops),
            "distance_km": round(km, 2),
            "eta_min": round(km / SPEED_KMPH * 60 + SERVICE_MIN * len(stops), 1),
            "algorithm": algo, "stops": stops, "path": path,
        })
    return {
        "routes": routes,
        "unassigned": [o["id"] for o in unassigned],
        "total_distance_km": round(total, 2),
        "compute_ms": round((time.perf_counter() - t0) * 1000, 1),
    }


def optimize_single(depot: dict, locations: List[dict], return_to_depot: bool = False) -> dict:
    """Stand-alone optimiser behind POST /api/optimize-route (one vehicle, N stops)."""
    points = {"S": (depot["lat"], depot["lng"])}
    points.update({f"L{i}": (p["lat"], p["lng"]) for i, p in enumerate(locations)})
    graph = RoadGraph.from_points(points, k=3)
    d = distance_matrix(graph, list(points))
    ids = [f"L{i}" for i in range(len(locations))]
    naive_km = route_cost("S", ids, d)
    order, km, algo = solve_open_tsp("S", ids, d)
    path, cur = [list(points["S"])], "S"
    for n in order + (["S"] if return_to_depot else []):
        _, seg = graph.shortest_path(cur, n)
        path += [list(graph.coords[x]) for x in seg[1:]]
        cur = n
    if return_to_depot and order:
        km += d[(order[-1], "S")]
    seq = [int(n[1:]) for n in order]
    return {
        "sequence": seq,
        "stops": [{"index": i, **locations[i]} for i in seq],
        "distance_km": round(km, 2),
        "unoptimized_km": round(naive_km, 2),
        "saved_pct": round(100 * (naive_km - km) / naive_km, 1) if naive_km > 0 else 0.0,
        "algorithm": algo,
        "path": path,
    }
