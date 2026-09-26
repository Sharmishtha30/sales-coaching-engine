import json
import sqlite3
from pathlib import Path


class Conflict(ValueError):
    pass


class Store:
    """One SQLite document per call; atomic compare-and-swap prevents lost updates."""
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, revision INTEGER NOT NULL, body TEXT NOT NULL)")
        path.chmod(0o600)

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def create(self, call):
        with self.connect() as db:
            db.execute("INSERT INTO calls VALUES (?, ?, ?)", (call["id"], call["revision"], json.dumps(call)))

    def get(self, call_id):
        with self.connect() as db:
            row = db.execute("SELECT body FROM calls WHERE id=?", (call_id,)).fetchone()
        if row is None:
            raise KeyError(call_id)
        return json.loads(row[0])

    def save(self, call):
        old = call["revision"]
        updated = {**call, "revision": old + 1}
        with self.connect() as db:
            cursor = db.execute("UPDATE calls SET revision=?, body=? WHERE id=? AND revision=?",
                                (old + 1, json.dumps(updated), call["id"], old))
            if cursor.rowcount != 1:
                raise Conflict("Call changed or was deleted; fetch its current revision")
        return updated

    def all(self):
        with self.connect() as db:
            rows = db.execute("SELECT body FROM calls").fetchall()
        return [json.loads(row[0]) for row in rows]

    def delete(self, call_id):
        call = self.get(call_id)
        with self.connect() as db:
            db.execute("DELETE FROM calls WHERE id=?", (call_id,))
        return call
