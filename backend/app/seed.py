"""Demo data: a hub in Hitech City, Hyderabad, three agents, ten parcels."""
import copy

DEPOT = {"name": "Central hub", "lat": 17.4435, "lng": 78.3772}

_AGENTS = [
    {"id": 1, "name": "Ravi", "color": "#0F8B8D", "capacity_kg": 30, "lat": 17.4440, "lng": 78.3760},
    {"id": 2, "name": "Anita", "color": "#E4572E", "capacity_kg": 24, "lat": 17.4428, "lng": 78.3785},
    {"id": 3, "name": "Imran", "color": "#6C4AB6", "capacity_kg": 20, "lat": 17.4432, "lng": 78.3770},
]

_ORDERS = [
    ("Gachibowli", 17.4401, 78.3489, 6, 2),
    ("Madhapur", 17.4486, 78.3908, 3, 1),
    ("Jubilee Hills", 17.4326, 78.4071, 8, 3),
    ("Kukatpally", 17.4948, 78.3996, 5, 1),
    ("Miyapur", 17.4969, 78.3548, 7, 2),
    ("Ameerpet", 17.4375, 78.4483, 4, 1),
    ("Banjara Hills", 17.4126, 78.4482, 9, 2),
    ("Begumpet", 17.4440, 78.4676, 2, 1),
    ("Secunderabad", 17.4399, 78.4983, 6, 3),
    ("Mehdipatnam", 17.3950, 78.4350, 5, 1),
]


def seed_agents():
    return copy.deepcopy(_AGENTS)


def seed_orders():
    return [
        {"id": i, "name": n, "lat": la, "lng": lo, "weight_kg": w, "priority": p, "status": "pending"}
        for i, (n, la, lo, w, p) in enumerate(_ORDERS, 1)
    ]
