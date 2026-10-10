import random
from contextlib import asynccontextmanager
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import cache, db
from .planner import optimize_single, plan_routes
from .seed import DEPOT, seed_agents, seed_orders


# ------------------------------------------------------------------ models
class Location(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    name: Optional[str] = None


class OptimizeRequest(BaseModel):
    depot: Optional[Location] = None
    locations: List[Location] = Field(min_length=1, max_length=40)
    return_to_depot: bool = False


class OrderIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    weight_kg: float = Field(default=3, gt=0, le=100)
    priority: int = Field(default=1, ge=1, le=3)


class StatusIn(BaseModel):
    status: Literal["pending", "delayed", "delivered"]


# ------------------------------------------------------------------ state + live hub
class Store:
    def __init__(self) -> None:
        self.agents = seed_agents()
        self.orders: dict = {}
        self.plan: dict = {}
        self.version = 0
        self.next_id = 1

    def load(self) -> None:
        rows = db.load_orders()
        if not rows:
            self.reset()
            return
        self.orders = {o["id"]: o for o in rows}
        self.next_id = max(self.orders) + 1
        self.replan()

    def reset(self) -> None:
        self.orders = {o["id"]: o for o in seed_orders()}
        self.next_id = max(self.orders) + 1
        db.replace_all(list(self.orders.values()))
        self.replan()

    def replan(self) -> None:
        self.plan = plan_routes(self.agents, list(self.orders.values()))
        self.version += 1
        cache.set_plan(self.plan)

    def snapshot(self) -> dict:
        return {
            "version": self.version,
            "depot": DEPOT,
            "agents": self.agents,
            "orders": sorted(self.orders.values(), key=lambda o: o["id"]),
            "plan": self.plan,
        }


class Hub:
    def __init__(self) -> None:
        self.clients: set = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.clients.discard(ws)

    async def broadcast(self, message: dict) -> None:
        for ws in list(self.clients):
            try:
                await ws.send_json(message)
            except Exception:
                self.clients.discard(ws)


store, hub = Store(), Hub()


async def push() -> dict:
    snap = store.snapshot()
    await hub.broadcast({"type": "state", "data": snap})
    return snap


@asynccontextmanager
async def lifespan(_: FastAPI):
    backend = db.init()
    redis_on = cache.init()
    store.load()
    print(f"[startup] database={backend} redis={'on' if redis_on else 'off'} orders={len(store.orders)}")
    yield


app = FastAPI(title="Smart Logistics & Route Optimization", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ------------------------------------------------------------------ REST
@app.get("/api/health")
def health():
    return {"status": "ok", "database": db.enabled, "redis": cache.enabled, "orders": len(store.orders)}


@app.get("/api/state")
def get_state():
    return store.snapshot()


@app.post("/api/optimize-route")
@app.post("/api/optimize-route/", include_in_schema=False)
def optimize(req: OptimizeRequest):
    depot = (req.depot or Location(**{k: DEPOT[k] for k in ("lat", "lng")})).model_dump()
    return optimize_single(depot, [l.model_dump() for l in req.locations], req.return_to_depot)


@app.post("/api/orders", status_code=201)
async def create_order(body: OrderIn):
    order = {"id": store.next_id, **body.model_dump(), "status": "pending"}
    store.next_id += 1
    store.orders[order["id"]] = order
    db.upsert(order)
    store.replan()
    snap = await push()
    return {"order": order, "plan": snap["plan"]}


@app.post("/api/simulate/order", status_code=201)
async def simulate_order():
    """Drop a random parcel somewhere in Hyderabad (demo button)."""
    body = OrderIn(
        name=f"Order #{store.next_id}",
        lat=round(random.uniform(17.37, 17.50), 5),
        lng=round(random.uniform(78.34, 78.56), 5),
        weight_kg=random.choice([2, 3, 4, 5, 6]),
        priority=random.choice([1, 1, 2, 3]),
    )
    return await create_order(body)


@app.patch("/api/orders/{order_id}/status")
async def set_status(order_id: int, body: StatusIn):
    order = store.orders.get(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    order["status"] = body.status
    db.upsert(order)
    store.replan()
    snap = await push()
    return {"order": order, "plan": snap["plan"]}


@app.delete("/api/orders/{order_id}")
async def delete_order(order_id: int):
    if order_id not in store.orders:
        raise HTTPException(404, "Order not found")
    del store.orders[order_id]
    db.remove(order_id)
    store.replan()
    await push()
    return {"deleted": order_id}


@app.post("/api/reset")
async def reset():
    store.reset()
    return await push()


# ------------------------------------------------------------------ WebSocket
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await hub.connect(ws)
    try:
        await ws.send_json({"type": "state", "data": store.snapshot()})
        while True:
            await ws.receive_text()   # keep-alive; server pushes updates
    except WebSocketDisconnect:
        hub.disconnect(ws)
