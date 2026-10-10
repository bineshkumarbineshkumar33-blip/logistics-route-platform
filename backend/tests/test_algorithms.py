import itertools
import random

from app.algorithms import (RoadGraph, distance_matrix, held_karp_open, knapsack,
                            nearest_neighbor, route_cost, solve_open_tsp, two_opt)


def small_graph():
    g = RoadGraph()
    for n in "ABCDE":
        g.add_node(n, (17.0 + ord(n) * 0.001, 78.0))
    for u, v, w in [("A", "B", 4), ("A", "C", 2), ("B", "C", 1), ("B", "D", 5), ("C", "D", 8), ("D", "E", 3)]:
        g.add_edge(u, v, w)
    return g


def test_dijkstra_known_graph():
    dist, _ = small_graph().dijkstra("A")
    assert dist["B"] == 3 and dist["D"] == 8 and dist["E"] == 11


def test_astar_matches_dijkstra_on_random_points():
    rnd = random.Random(7)
    pts = {f"N{i}": (17.35 + rnd.random() * 0.15, 78.3 + rnd.random() * 0.25) for i in range(25)}
    g = RoadGraph.from_points(pts, k=3)
    for _ in range(15):
        a, b = rnd.sample(list(pts), 2)
        dj = g.dijkstra(a)[0][b]
        km, path = g.astar(a, b)
        assert abs(dj - km) < 1e-9 and path[0] == a and path[-1] == b


def make_matrix(n, seed=3):
    rnd = random.Random(seed)
    pts = {"S": (17.44, 78.37)}
    pts.update({f"L{i}": (17.35 + rnd.random() * 0.15, 78.3 + rnd.random() * 0.25) for i in range(n)})
    g = RoadGraph.from_points(pts)
    return distance_matrix(g, list(pts)), [f"L{i}" for i in range(n)]


def test_held_karp_is_optimal_vs_bruteforce():
    d, stops = make_matrix(6)
    _, cost = held_karp_open("S", stops, d)
    brute = min(route_cost("S", p, d) for p in itertools.permutations(stops))
    assert abs(cost - brute) < 1e-9


def test_two_opt_not_worse_than_nearest_neighbor():
    d, stops = make_matrix(12)
    nn = nearest_neighbor("S", stops, d)
    assert route_cost("S", two_opt("S", nn, d), d) <= route_cost("S", nn, d) + 1e-9
    assert solve_open_tsp("S", stops, d)[2] == "nearest-neighbor + 2-opt"


def test_knapsack_optimal():
    chosen, best = knapsack([("a", 5, 10), ("b", 4, 40), ("c", 6, 30), ("d", 3, 50)], 10)
    assert best == 90 and set(chosen) == {"b", "d"}
