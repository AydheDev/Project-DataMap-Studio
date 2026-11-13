import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat()

class Store:
    def __init__(self, root: Path):
        self.root = root
        for directory in ("uploads", "outputs", "temp"):
            (root / directory).mkdir(parents=True, exist_ok=True)
        self.db = root / "datamap.sqlite3"
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS uploads(id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS templates(id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS preferences(id TEXT PRIMARY KEY, data TEXT NOT NULL);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db, timeout=30)
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def put(self, table, key, value):
        if table not in {"uploads", "jobs", "templates", "preferences"}:
            raise ValueError("Unknown storage collection")
        with self.connect() as db:
            db.execute(f"INSERT OR REPLACE INTO {table}(id,data) VALUES(?,?)", (key, json.dumps(value)))

    def get(self, table, key):
        if table not in {"uploads", "jobs", "templates", "preferences"}:
            raise ValueError("Unknown storage collection")
        with self.connect() as db:
            row = db.execute(f"SELECT data FROM {table} WHERE id=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, table):
        if table not in {"uploads", "jobs", "templates", "preferences"}:
            raise ValueError("Unknown storage collection")
        with self.connect() as db:
            rows = db.execute(f"SELECT data FROM {table} ORDER BY rowid DESC").fetchall()
        return [json.loads(row[0]) for row in rows]

    def recover(self):
        for job in self.list("jobs"):
            if job["status"] in ("queued", "running"):
                job.update(status="failed", error="Processing was interrupted. Start a new job.", finished_at=now())
                self.put("jobs", job["id"], job)
        # Only generated partial files in owned directories are eligible for cleanup.
        for directory in ("temp", "outputs"):
            for file in (self.root / directory).glob("*.tmp"):
                if file.is_file():
                    file.unlink(missing_ok=True)
