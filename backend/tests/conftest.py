import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["REDIS_URL"] = "redis://localhost:1/0"   # unreachable on purpose -> cache disabled
