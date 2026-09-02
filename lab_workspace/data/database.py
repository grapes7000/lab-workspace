import csv
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from lab_workspace.core.config import DATABASE_PATH, ensure_directories


WORKSPACE_DOCUMENTS = {
    "scratchpad": "Scratchpad",
    "final": "Final Document",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, title TEXT NOT NULL, current_text TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS revisions (id INTEGER PRIMARY KEY, document_key TEXT NOT NULL, text TEXT NOT NULL, created_at TEXT NOT NULL, reason TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_revisions_key ON revisions(document_key, id DESC);
CREATE TABLE IF NOT EXISTS deleted_fragments (id INTEGER PRIMARY KEY, document_key TEXT NOT NULL, fragment TEXT NOT NULL, position INTEGER NOT NULL, deleted_at TEXT NOT NULL, recovered_at TEXT);
CREATE INDEX IF NOT EXISTS idx_deleted_fragments_key ON deleted_fragments(document_key, id DESC);
CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, archived_at TEXT);
CREATE INDEX IF NOT EXISTS idx_workspaces_active ON workspaces(archived_at, updated_at DESC, id DESC);
CREATE TABLE IF NOT EXISTS materials (id INTEGER PRIMARY KEY, code TEXT UNIQUE, name TEXT NOT NULL, formula TEXT, mw REAL, density REAL, density_unit TEXT, form TEXT, purity REAL, active_fraction REAL, aliases TEXT, tags TEXT, notes TEXT, created_at TEXT, updated_at TEXT, superseded_at TEXT);
CREATE TABLE IF NOT EXISTS material_revisions (id INTEGER PRIMARY KEY, material_id INTEGER, snapshot_json TEXT, changed_at TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS samples (id INTEGER PRIMARY KEY, code TEXT UNIQUE, name TEXT NOT NULL, sample_type TEXT, project TEXT, status TEXT, source TEXT, collection_location TEXT, collection_date TEXT, received_date TEXT, fuel_grade TEXT, nominal_ethanol REAL, lot_number TEXT, quantity REAL, quantity_unit TEXT, container TEXT, storage_location TEXT, parent_sample_code TEXT, tags TEXT, notes TEXT, created_at TEXT, updated_at TEXT, superseded_at TEXT);
CREATE TABLE IF NOT EXISTS sample_revisions (id INTEGER PRIMARY KEY, sample_id INTEGER, snapshot_json TEXT, changed_at TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS calculations (id INTEGER PRIMARY KEY, title TEXT, input_json TEXT, result_json TEXT, markdown TEXT, created_at TEXT, engine_version TEXT);
CREATE TABLE IF NOT EXISTS imports (id INTEGER PRIMARY KEY, filename TEXT, file_hash TEXT, format TEXT, imported_at TEXT, rows_added INTEGER, rows_skipped INTEGER, warnings_json TEXT);
CREATE TRIGGER IF NOT EXISTS revisions_no_delete BEFORE DELETE ON revisions BEGIN SELECT RAISE(ABORT, 'Revision history is append-only'); END;
CREATE TRIGGER IF NOT EXISTS revisions_no_update BEFORE UPDATE ON revisions BEGIN SELECT RAISE(ABORT, 'Revision history is immutable'); END;
CREATE TRIGGER IF NOT EXISTS deleted_fragments_no_delete BEFORE DELETE ON deleted_fragments BEGIN SELECT RAISE(ABORT, 'Deleted-text history is append-only'); END;
CREATE TRIGGER IF NOT EXISTS no_delete_mat_rev BEFORE DELETE ON material_revisions BEGIN SELECT RAISE(ABORT, 'history is append-only'); END;
CREATE TRIGGER IF NOT EXISTS no_delete_sample_rev BEFORE DELETE ON sample_revisions BEGIN SELECT RAISE(ABORT, 'history is append-only'); END;
CREATE TRIGGER IF NOT EXISTS no_delete_calc BEFORE DELETE ON calculations BEGIN SELECT RAISE(ABORT, 'history is append-only'); END;
"""


def now():
    return datetime.now().isoformat(timespec="seconds")


class Database:
    def __init__(self):
        ensure_directories()
        with self.connect() as connection:
            connection.executescript(SCHEMA)
        # Keep the legacy document keys intact so existing installations and
        # older exports remain readable. Named workspaces use namespaced keys.
        self.ensure_document("scratchpad", "Scratchpad")
        self.ensure_document("final", "Final Document")
        self.ensure_default_workspace()

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
            if not row:
                raise KeyError(key)
            if row["current_text"] == text and not force_revision:
                return False
            timestamp = now()
            connection.execute(
                "UPDATE documents SET current_text=?, updated_at=? WHERE key=?",
                (text, timestamp, key),
            )
            connection.execute(
                "INSERT INTO revisions(document_key,text,created_at,reason) VALUES(?,?,?,?)",
                (key, text, timestamp, reason),
            )
        return True

    def revisions(self, key, limit=100):
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM revisions WHERE document_key=? ORDER BY id DESC LIMIT ?",
                (key, limit),
            ).fetchall()

    def revision(self, revision_id):
        with self.connect() as connection:
            return connection.execute("SELECT * FROM revisions WHERE id=?", (revision_id,)).fetchone()

    def record_deleted_fragment(self, key, fragment, position):
        if not fragment:
            return None
        with self.connect() as connection:
            return int(
                connection.execute(
                    "INSERT INTO deleted_fragments(document_key,fragment,position,deleted_at) VALUES(?,?,?,?)",
                    (key, fragment, position, now()),
                ).lastrowid
            )

    def latest_deleted_fragment(self, key="scratchpad", include_recovered=False):
        with self.connect() as connection:
            if include_recovered:
                return connection.execute(
                    "SELECT * FROM deleted_fragments WHERE document_key=? ORDER BY id DESC LIMIT 1",
                    (key,),
                ).fetchone()
            return connection.execute(
                "SELECT * FROM deleted_fragments WHERE document_key=? AND recovered_at IS NULL ORDER BY id DESC LIMIT 1",
                (key,),
            ).fetchone()

    def unrecovered_deleted_fragments(self, key="scratchpad"):
        """Return pending deletions in recovery order (newest first)."""
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM deleted_fragments WHERE document_key=? AND recovered_at IS NULL ORDER BY id DESC",
                (key,),
            ).fetchall()

    def mark_fragment_recovered(self, fragment_id):
        with self.connect() as connection:
            connection.execute(
                "UPDATE deleted_fragments SET recovered_at=? WHERE id=? AND recovered_at IS NULL",
                (now(), fragment_id),
            )

    # ---- Named workspaces -------------------------------------------------

    def workspace_document_key(self, workspace_id, document_type):
        if document_type not in WORKSPACE_DOCUMENTS:
            raise ValueError(f"Unsupported workspace document type: {document_type}")
        return f"workspace:{int(workspace_id)}:{document_type}"

    def ensure_workspace_documents(self, workspace_id):
        for document_type, title in WORKSPACE_DOCUMENTS.items():
            self.ensure_document(self.workspace_document_key(workspace_id, document_type), title)

    def create_workspace(self, name):
        clean_name = (name or "").strip() or "Untitled Workspace"
        timestamp = now()
        with self.connect() as connection:
            workspace_id = int(
                connection.execute(
                    "INSERT INTO workspaces(name,created_at,updated_at) VALUES(?,?,?)",
                    (clean_name, timestamp, timestamp),
                ).lastrowid
            )
        self.ensure_workspace_documents(workspace_id)
        return workspace_id

    def ensure_default_workspace(self):
        rows = self.list_workspaces()
        if rows:
            workspace_id = int(rows[-1]["id"])
            self.ensure_workspace_documents(workspace_id)
            return workspace_id
        workspace_id = self.create_workspace("Default Workspace")
        self._copy_legacy_writing_into_workspace(workspace_id)
        return workspace_id

    def _copy_legacy_writing_into_workspace(self, workspace_id):
        """Copy v1.x global writing state/history into the first workspace once."""
        with self.connect() as connection:
            for document_type, title in WORKSPACE_DOCUMENTS.items():
                legacy_key = document_type
                workspace_key = self.workspace_document_key(workspace_id, document_type)
                legacy = connection.execute(
                    "SELECT current_text, updated_at FROM documents WHERE key=?",
                    (legacy_key,),
                ).fetchone()
                if legacy:
                    connection.execute(
                        "UPDATE documents SET current_text=?, updated_at=?, title=? WHERE key=?",
                        (legacy["current_text"], legacy["updated_at"], title, workspace_key),
                    )
                    connection.execute(
                        "INSERT INTO revisions(document_key,text,created_at,reason) "
                        "SELECT ?,text,created_at,reason FROM revisions WHERE document_key=?",
                        (workspace_key, legacy_key),
                    )
                    connection.execute(
                        "INSERT INTO deleted_fragments(document_key,fragment,position,deleted_at,recovered_at) "
                        "SELECT ?,fragment,position,deleted_at,recovered_at FROM deleted_fragments WHERE document_key=?",
                        (workspace_key, legacy_key),
                    )

    def list_workspaces(self, include_archived=False):
        with self.connect() as connection:
            if include_archived:
                return connection.execute(
                    "SELECT * FROM workspaces ORDER BY updated_at DESC, id DESC"
                ).fetchall()
            return connection.execute(
                "SELECT * FROM workspaces WHERE archived_at IS NULL ORDER BY updated_at DESC, id DESC"
            ).fetchall()

    def workspace(self, workspace_id):
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM workspaces WHERE id=?", (int(workspace_id),)
            ).fetchone()

    def rename_workspace(self, workspace_id, name):
        clean_name = (name or "").strip()
        if not clean_name:
            raise ValueError("Workspace name cannot be empty.")
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE workspaces SET name=?, updated_at=? WHERE id=? AND archived_at IS NULL",
                (clean_name, now(), int(workspace_id)),
            )
            if cursor.rowcount == 0:
                raise KeyError(workspace_id)

    def touch_workspace(self, workspace_id):
        with self.connect() as connection:
            connection.execute(
                "UPDATE workspaces SET updated_at=? WHERE id=?",
                (now(), int(workspace_id)),
            )

    def get_workspace_text(self, workspace_id, document_type):
        self.ensure_workspace_documents(workspace_id)
        return self.get_text(self.workspace_document_key(workspace_id, document_type))

    def save_workspace_text(
        self, workspace_id, document_type, text, reason="autosave", force_revision=False
    ):
        self.ensure_workspace_documents(workspace_id)
        changed = self.save_text(
            self.workspace_document_key(workspace_id, document_type),
            text,
            reason,
            force_revision,
        )
        if changed:
            self.touch_workspace(workspace_id)
        return changed

    # ---- Existing laboratory data ---------------------------------------

    def next_code(self, table, prefix):
        queries = {
            "materials": "SELECT COALESCE(MAX(id),0)+1 FROM materials",
            "samples": "SELECT COALESCE(MAX(id),0)+1 FROM samples",
        }
        if table not in queries:
            raise ValueError(f"Unsupported code table: {table}")
        with self.connect() as connection:
            number = connection.execute(queries[table]).fetchone()[0]
        return f"{prefix}-{datetime.now().year}-{number:04d}"

    def save_material(self, data):
        code, timestamp = data.get("code") or self.next_code("materials", "MAT"), now()
        values = (
            data["name"],
            data.get("formula", ""),
            data.get("mw"),
            data.get("density"),
            data.get("density_unit", "g/mL"),
            data.get("form", "Other"),
            data.get("purity", 100),
            data.get("active_fraction", 100),
            data.get("aliases", ""),
            data.get("tags", ""),
            data.get("notes", ""),
            timestamp,
            code,
        )
        with self.connect() as connection:
            existing = connection.execute("SELECT * FROM materials WHERE code=?", (code,)).fetchone()
            if existing:
                connection.execute(
                    "INSERT INTO material_revisions(material_id,snapshot_json,changed_at,reason) VALUES(?,?,?,?)",
                    (existing["id"], json.dumps(dict(existing)), timestamp, "updated"),
                )
                connection.execute(
                    "UPDATE materials SET name=?,formula=?,mw=?,density=?,density_unit=?,form=?,purity=?,active_fraction=?,aliases=?,tags=?,notes=?,updated_at=? WHERE code=?",
                    values,
                )
            else:
                connection.execute(
                    "INSERT INTO materials(code,name,formula,mw,density,density_unit,form,purity,active_fraction,aliases,tags,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (code, *values[:-1], timestamp),
                )
        return code

    def save_sample(self, data):
        code, timestamp = data.get("code") or self.next_code("samples", "SMP"), now()
        fields = (
            "name",
            "sample_type",
            "project",
            "status",
            "source",
            "collection_location",
            "collection_date",
            "received_date",
            "fuel_grade",
            "nominal_ethanol",
            "lot_number",
            "quantity",
            "quantity_unit",
            "container",
            "storage_location",
            "parent_sample_code",
            "tags",
            "notes",
        )
        values = tuple(data.get(field, "") for field in fields)
        with self.connect() as connection:
            existing = connection.execute("SELECT * FROM samples WHERE code=?", (code,)).fetchone()
            if existing:
                connection.execute(
                    "INSERT INTO sample_revisions(sample_id,snapshot_json,changed_at,reason) VALUES(?,?,?,?)",
                    (existing["id"], json.dumps(dict(existing)), timestamp, "updated"),
                )
                connection.execute(
                    "UPDATE samples SET name=?,sample_type=?,project=?,status=?,source=?,collection_location=?,collection_date=?,received_date=?,fuel_grade=?,nominal_ethanol=?,lot_number=?,quantity=?,quantity_unit=?,container=?,storage_location=?,parent_sample_code=?,tags=?,notes=?,updated_at=? WHERE code=?",
                    (*values, timestamp, code),
                )
            else:
                connection.execute(
                    "INSERT INTO samples(code,name,sample_type,project,status,source,collection_location,collection_date,received_date,fuel_grade,nominal_ethanol,lot_number,quantity,quantity_unit,container,storage_location,parent_sample_code,tags,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (code, *values, timestamp, timestamp),
                )
        return code

    def search(self, table, term=""):
        pattern = f"%{term}%"
        with self.connect() as connection:
            if table == "materials":
                return connection.execute(
                    "SELECT * FROM materials WHERE name LIKE ? OR formula LIKE ? OR aliases LIKE ? OR tags LIKE ? OR notes LIKE ? OR code LIKE ? ORDER BY id DESC",
                    (pattern,) * 6,
                ).fetchall()
            if table == "samples":
                return connection.execute(
                    "SELECT * FROM samples WHERE name LIKE ? OR sample_type LIKE ? OR project LIKE ? OR source LIKE ? OR fuel_grade LIKE ? OR lot_number LIKE ? OR tags LIKE ? OR notes LIKE ? OR code LIKE ? ORDER BY id DESC",
                    (pattern,) * 9,
                ).fetchall()
        raise ValueError(f"Unsupported table: {table}")

    def save_calculation(self, title, inputs, result, markdown):
        with self.connect() as connection:
            return connection.execute(
                "INSERT INTO calculations(title,input_json,result_json,markdown,created_at,engine_version) VALUES(?,?,?,?,?,?)",
                (title, json.dumps(inputs), json.dumps(result), markdown, now(), "combined-1"),
            ).lastrowid

    def export_csv(self, table, path):
        rows = self.search(table, "")
        if not rows:
            return 0
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(dict(row) for row in rows)
        return len(rows)

    def import_csv(self, table, path):
        added = skipped = 0
        warnings = []
        with open(path, newline="", encoding="utf-8-sig") as file:
            for number, row in enumerate(csv.DictReader(file), 2):
                try:
                    if table == "materials":
                        for key in ("mw", "density", "purity", "active_fraction"):
                            row[key] = float(row[key]) if row.get(key) else None
                        if not row.get("name"):
                            raise ValueError("name required")
                        self.save_material(row)
                    elif table == "samples":
                        if not row.get("name"):
                            raise ValueError("name required")
                        self.save_sample(row)
                    else:
                        raise ValueError(f"Unsupported table: {table}")
                    added += 1
                except Exception as error:
                    skipped += 1
                    warnings.append(f"Row {number}: {error}")
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO imports(filename,file_hash,format,imported_at,rows_added,rows_skipped,warnings_json) VALUES(?,?,?,?,?,?,?)",
                (str(path), digest, "csv", now(), added, skipped, json.dumps(warnings)),
            )
        return added, skipped, warnings
