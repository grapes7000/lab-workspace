import importlib
import os
import sqlite3
import tempfile
import unittest


class WorkspaceTests(unittest.TestCase):
    def load_database(self, directory):
        os.environ["LAB_WORKSPACE_DATA_DIR"] = directory
        import lab_workspace.core.config as config
        importlib.reload(config)
        import lab_workspace.data.database as database
        importlib.reload(database)
        return database.Database()

    def test_named_workspaces_keep_writing_isolated(self):
        with tempfile.TemporaryDirectory() as directory:
            db = self.load_database(directory)
            first = int(db.list_workspaces()[0]["id"])
            second = db.create_workspace("Experiment B")
            db.save_workspace_text(first, "scratchpad", "alpha")
            db.save_workspace_text(second, "scratchpad", "beta")
            db.save_workspace_text(first, "final", "# A")
            db.save_workspace_text(second, "final", "# B")
            self.assertEqual(db.get_workspace_text(first, "scratchpad"), "alpha")
            self.assertEqual(db.get_workspace_text(second, "scratchpad"), "beta")
            self.assertEqual(db.get_workspace_text(first, "final"), "# A")
            self.assertEqual(db.get_workspace_text(second, "final"), "# B")

    def test_workspace_rename_does_not_change_document_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            db = self.load_database(directory)
            workspace_id = db.create_workspace("Before")
            key = db.workspace_document_key(workspace_id, "scratchpad")
            db.save_workspace_text(workspace_id, "scratchpad", "notes")
            db.rename_workspace(workspace_id, "After")
            self.assertEqual(db.workspace(workspace_id)["name"], "After")
            self.assertEqual(db.get_text(key), "notes")

    def test_first_workspace_migrates_legacy_writing_and_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "lab_workspace_combined.db")
            connection = sqlite3.connect(path)
            connection.executescript(
                """
                CREATE TABLE documents (id INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, title TEXT NOT NULL, current_text TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL);
                CREATE TABLE revisions (id INTEGER PRIMARY KEY, document_key TEXT NOT NULL, text TEXT NOT NULL, created_at TEXT NOT NULL, reason TEXT NOT NULL);
                CREATE TABLE deleted_fragments (id INTEGER PRIMARY KEY, document_key TEXT NOT NULL, fragment TEXT NOT NULL, position INTEGER NOT NULL, deleted_at TEXT NOT NULL, recovered_at TEXT);
                INSERT INTO documents(key,title,current_text,updated_at) VALUES('scratchpad','Scratchpad','legacy scratch','2026-09-01T12:00:00');
                INSERT INTO documents(key,title,current_text,updated_at) VALUES('final','Final Document','# Legacy final','2026-09-01T12:00:00');
                INSERT INTO revisions(document_key,text,created_at,reason) VALUES('scratchpad','old scratch','2026-09-01T11:00:00','autosave');
                INSERT INTO deleted_fragments(document_key,fragment,position,deleted_at,recovered_at) VALUES('scratchpad','gone',2,'2026-09-01T11:30:00',NULL);
                """
            )
            connection.commit()
            connection.close()
            db = self.load_database(directory)
            workspace_id = int(db.list_workspaces()[0]["id"])
            scratch_key = db.workspace_document_key(workspace_id, "scratchpad")
            self.assertEqual(db.get_workspace_text(workspace_id, "scratchpad"), "legacy scratch")
            self.assertEqual(db.get_workspace_text(workspace_id, "final"), "# Legacy final")
            self.assertEqual(db.revisions(scratch_key)[0]["text"], "old scratch")
            self.assertEqual(db.latest_deleted_fragment(scratch_key)["fragment"], "gone")

    def test_workspace_document_type_is_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            db = self.load_database(directory)
            workspace_id = int(db.list_workspaces()[0]["id"])
            with self.assertRaises(ValueError):
                db.workspace_document_key(workspace_id, "../../bad")


if __name__ == "__main__":
    unittest.main()
