"""Optional Redis cache for the latest plan (fast reads for live tracking).
If Redis is not running the app keeps working without it."""
import json
import os

enabled = False
_r = None


def init() -> bool:
    global enabled, _r
    try:
        import redis

        _r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                                  socket_connect_timeout=0.3, socket_timeout=0.3)
        _r.ping()
        enabled = True
    except Exception:
        enabled = False
    return enabled


def set_plan(plan: dict) -> None:
    if enabled:
        try:
            _r.set("plan:latest", json.dumps(plan))
        except Exception:
            pass


def get_plan():
    if enabled:
        try:
            raw = _r.get("plan:latest")
            return json.loads(raw) if raw else None
        except Exception:
            return None
    return None
