import sqlite3
from contextlib import contextmanager
from datetime import datetime
from lab_workspace.core.config import DATABASE_PATH, ensure_directories

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
 id INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
 current_text TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS revisions (
 id INTEGER PRIMARY KEY, document_key TEXT NOT NULL, text TEXT NOT NULL,
 created_at TEXT NOT NULL, reason TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_revisions_key ON revisions(document_key, id DESC);
"""


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Database:
    def __init__(self):
        ensure_directories()
        with self.connect() as connection:
            connection.executescript(SCHEMA)
        self.ensure_document("scratchpad", "Scratchpad")
        self.ensure_document("final", "Final Document")

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def ensure_document(self, key, title):
        with self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO documents(key,title,current_text,updated_at) VALUES(?,?,?,?)",
                (key, title, "", now()),
            )

    def get_text(self, key):
        with self.connect() as connection:
            row = connection.execute("SELECT current_text FROM documents WHERE key=?", (key,)).fetchone()
        return row["current_text"] if row else ""

    def save_text(self, key, text, reason="autosave", force_revision=False):
        with self.connect() as connection:
            row = connection.execute("SELECT current_text FROM documents WHERE key=?", (key,)).fetchone()
            if not row: raise KeyError(key)
            if row["current_text"] == text and not force_revision: return False
            timestamp = now()
            connection.execute("UPDATE documents SET current_text=?, updated_at=? WHERE key=?", (text, timestamp, key))
            connection.execute("INSERT INTO revisions(document_key,text,created_at,reason) VALUES(?,?,?,?)", (key, text, timestamp, reason))
        return True

    def revisions(self, key, limit=100):
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM revisions WHERE document_key=? ORDER BY id DESC LIMIT ?", (key, limit)
            ).fetchall()

    def revision(self, revision_id):
        with self.connect() as connection:
            return connection.execute("SELECT * FROM revisions WHERE id=?", (revision_id,)).fetchone()
