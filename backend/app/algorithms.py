"""Core DSA module - pure Python, no framework imports.

Contents
  RoadGraph        weighted undirected graph + Dijkstra + A*
  distance_matrix  all-pairs shortest paths between delivery points
  held_karp_open   exact TSP (DP over bitmasks) for small stop counts
  nearest_neighbor + two_opt   heuristic TSP for larger stop counts
  knapsack         0/1 knapsack to choose which parcels fit in a vehicle
"""
from __future__ import annotations

import heapq
import itertools
import math
from typing import Dict, List, Sequence, Tuple

Coord = Tuple[float, float]  # (lat, lng)
INF = math.inf


def haversine_km(a: Coord, b: Coord) -> float:
    r = 6371.0088
    la1, lo1 = map(math.radians, a)
    la2, lo2 = map(math.radians, b)
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


class RoadGraph:
    """Nodes = places, edges = roads weighted by km."""

    def __init__(self) -> None:
        self.coords: Dict[str, Coord] = {}
        self.adj: Dict[str, Dict[str, float]] = {}

    def add_node(self, node: str, coord: Coord) -> None:
        self.coords[node] = coord
        self.adj.setdefault(node, {})

    def add_edge(self, u: str, v: str, w: float) -> None:
        if v not in self.adj[u] or w < self.adj[u][v]:
            self.adj[u][v] = w
            self.adj[v][u] = w

    @classmethod
    def from_points(cls, points: Dict[str, Coord], k: int = 3, road_factor: float = 1.3) -> "RoadGraph":
        """Build a connected road network: k-nearest-neighbour edges + a minimum
        spanning tree (Kruskal + union-find) so every node is reachable.
        road_factor >= 1 models roads being longer than straight lines, which also
        keeps the haversine heuristic in A* admissible."""
        g = cls()
        for n, c in points.items():
            g.add_node(n, c)
        ids = list(points)

        def w(a: str, b: str) -> float:
            return haversine_km(points[a], points[b]) * road_factor

        for a in ids:
            for b in sorted((x for x in ids if x != a), key=lambda x: w(a, x))[:k]:
                g.add_edge(a, b, w(a, b))

        parent = {n: n for n in ids}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for wt, a, b in sorted((w(a, b), a, b) for a, b in itertools.combinations(ids, 2)):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
                g.add_edge(a, b, wt)
        return g

    def dijkstra(self, src: str, dst: str | None = None):
        """Min-heap Dijkstra. Returns (dist, prev). O((V+E) log V)."""
        dist = {src: 0.0}
        prev: Dict[str, str] = {}
        pq = [(0.0, src)]
        done = set()
        while pq:
            d, u = heapq.heappop(pq)
            if u in done:
                continue
            done.add(u)
            if u == dst:
                break
            for v, w in self.adj[u].items():
                nd = d + w
                if nd < dist.get(v, INF):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        return dist, prev

    def astar(self, src: str, dst: str) -> Tuple[float, List[str]]:
        """A* with a straight-line (haversine) heuristic. Returns (km, node path)."""
        goal = self.coords[dst]

        def h(n: str) -> float:
            return haversine_km(self.coords[n], goal)

        g = {src: 0.0}
        prev: Dict[str, str] = {}
        pq = [(h(src), src)]
        closed = set()
        while pq:
            _, u = heapq.heappop(pq)
            if u == dst:
                return g[u], self._path(prev, src, dst)
            if u in closed:
                continue
            closed.add(u)
            for v, w in self.adj[u].items():
                ng = g[u] + w
                if ng < g.get(v, INF):
                    g[v] = ng
                    prev[v] = u
                    heapq.heappush(pq, (ng + h(v), v))
        return INF, []

    @staticmethod
    def _path(prev: Dict[str, str], src: str, dst: str) -> List[str]:
        path = [dst]
        while path[-1] != src:
            path.append(prev[path[-1]])
        return path[::-1]

    def shortest_path(self, src: str, dst: str) -> Tuple[float, List[str]]:
        return self.astar(src, dst)


def distance_matrix(graph: RoadGraph, ids: Sequence[str]) -> Dict[Tuple[str, str], float]:
    m: Dict[Tuple[str, str], float] = {}
    for a in ids:
        dist, _ = graph.dijkstra(a)
        for b in ids:
            m[(a, b)] = dist.get(b, INF)
    return m


# ---------------------------------------------------------------- routing (TSP)
Dist = Dict[Tuple[str, str], float]


def route_cost(start: str, order: Sequence[str], d: Dist) -> float:
    cost, cur = 0.0, start
    for n in order:
        cost += d[(cur, n)]
        cur = n
    return cost


def held_karp_open(start: str, stops: Sequence[str], d: Dist) -> Tuple[List[str], float]:
    """Exact shortest open path from `start` visiting every stop once. O(n^2 * 2^n)."""
    n = len(stops)
    if n == 0:
        return [], 0.0
    dp = [[INF] * n for _ in range(1 << n)]
    par = [[-1] * n for _ in range(1 << n)]
    for j in range(n):
        dp[1 << j][j] = d[(start, stops[j])]
    for mask in range(1, 1 << n):
        for j in range(n):
            if not (mask >> j) & 1 or dp[mask][j] == INF:
                continue
            for k in range(n):
                if (mask >> k) & 1:
                    continue
                nm = mask | (1 << k)
                c = dp[mask][j] + d[(stops[j], stops[k])]
                if c < dp[nm][k]:
                    dp[nm][k] = c
                    par[nm][k] = j
    full = (1 << n) - 1
    j = min(range(n), key=lambda x: dp[full][x])
    best, order, mask = dp[full][j], [], full
    while j != -1:
        order.append(stops[j])
        pj = par[mask][j]
        mask ^= 1 << j
        j = pj
    return order[::-1], best


def nearest_neighbor(start: str, stops: Sequence[str], d: Dist) -> List[str]:
    left, order, cur = list(stops), [], start
    while left:
        nxt = min(left, key=lambda s: d[(cur, s)])
        order.append(nxt)
        left.remove(nxt)
        cur = nxt
    return order


def two_opt(start: str, order: List[str], d: Dist) -> List[str]:
    """Repeatedly reverse segments while that shortens the route."""
    best = order[:]
    improved = True
    while improved:
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                cand = best[:i] + best[i : j + 1][::-1] + best[j + 1 :]
                if route_cost(start, cand, d) < route_cost(start, best, d) - 1e-9:
                    best, improved = cand, True
    return best


def solve_open_tsp(start: str, stops: Sequence[str], d: Dist, exact_limit: int = 9):
    if len(stops) <= exact_limit:
        order, cost = held_karp_open(start, stops, d)
        return order, cost, "held-karp (exact)"
    order = two_opt(start, nearest_neighbor(start, stops, d), d)
    return order, route_cost(start, order, d), "nearest-neighbor + 2-opt"


# ---------------------------------------------------------------- load (knapsack)
def knapsack(items: Sequence[Tuple[object, int, int]], capacity: int):
    """0/1 knapsack. items = (key, integer_weight, value). Returns (chosen_keys, best_value)."""
    n = len(items)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i, (_, w, v) in enumerate(items, 1):
        for c in range(capacity + 1):
            dp[i][c] = dp[i - 1][c]
            if w <= c:
                dp[i][c] = max(dp[i][c], dp[i - 1][c - w] + v)
    chosen, c = [], capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            chosen.append(items[i - 1][0])
            c -= items[i - 1][1]
    return chosen[::-1], dp[n][capacity]
