"""Persistence. Defaults to SQLite so the project runs with zero setup.
Set DATABASE_URL=postgresql+psycopg2://logistics:logistics@localhost:5432/logistics
to use PostgreSQL/PostGIS (see docker-compose.yml)."""
import os
from typing import List

from sqlalchemy import Column, Float, Integer, String, create_engine, delete, select
from sqlalchemy.orm import declarative_base, sessionmaker

URL = os.getenv("DATABASE_URL", "sqlite:///./logistics.db")
engine = create_engine(
    URL,
    connect_args={"check_same_thread": False} if URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
Session = sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()
enabled = True


class OrderRow(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    priority = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="pending")


def _to_dict(r: OrderRow) -> dict:
    return {c: getattr(r, c) for c in ("id", "name", "lat", "lng", "weight_kg", "priority", "status")}


def init() -> str:
    global enabled
    try:
        Base.metadata.create_all(engine)
        enabled = True
        return URL.split("://")[0]
    except Exception as exc:  # database not reachable -> keep running in memory
        enabled = False
        print(f"[db] disabled ({exc.__class__.__name__}); running in memory only")
        return "memory"


def load_orders() -> List[dict]:
    if not enabled:
        return []
    with Session() as s:
        return [_to_dict(r) for r in s.scalars(select(OrderRow).order_by(OrderRow.id))]


def upsert(order: dict) -> None:
    if enabled:
        with Session.begin() as s:
            s.merge(OrderRow(**order))


def remove(order_id: int) -> None:
    if enabled:
        with Session.begin() as s:
            s.execute(delete(OrderRow).where(OrderRow.id == order_id))


def replace_all(orders: List[dict]) -> None:
    if enabled:
        with Session.begin() as s:
            s.execute(delete(OrderRow))
            s.add_all(OrderRow(**o) for o in orders)
