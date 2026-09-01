import os, tempfile, unittest
from pathlib import Path

class HistoryDesignTests(unittest.TestCase):
    def test_schema_contains_immutable_history_triggers(self):
        source = Path(__file__).parents[1] / "lab_workspace" / "data" / "database.py"
        text = source.read_text(encoding="utf-8")
        self.assertIn("revisions_no_delete", text)
        self.assertIn("revisions_no_update", text)
        self.assertIn("deleted_fragments_no_delete", text)

if __name__ == "__main__": unittest.main()
