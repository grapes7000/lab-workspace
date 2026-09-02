import os
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from lab_workspace.ui.scratchpad_panel import ScratchpadPanel


class ScratchpadDeletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.panel = ScratchpadPanel("Scratchpad", "Notes")
        self.panel.set_initial_text("abcd")
        self.groups = []
        self.panel.deletion_grouped.connect(
            lambda fragment, position: self.groups.append((fragment, position))
        )

    def test_adjacent_backspaces_become_one_group(self):
        self.panel.editor.setPlainText("abc")
        self.panel.editor.setPlainText("ab")
        self.panel.flush_deletion_group()
        self.assertEqual(self.groups, [("cd", 2)])

    def test_disjoint_deletions_become_separate_groups(self):
        self.panel.editor.setPlainText("abc")
        self.panel.editor.setPlainText("bc")
        self.panel.flush_deletion_group()
        self.assertEqual(self.groups, [("d", 3), ("a", 0)])

    def test_recovery_removes_only_the_recovered_ghost(self):
        self.panel.commit_ghost(1, "first", 0)
        self.panel.commit_ghost(2, "second", 2)
        self.panel.remove_ghost(2)
        self.assertEqual(
            self.panel.latest_ghost(),
            {"id": 1, "fragment": "first", "position": 0},
        )


if __name__ == "__main__":
    unittest.main()
