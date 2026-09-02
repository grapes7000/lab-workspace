import unittest


class SafeDockingDesignTests(unittest.TestCase):
    def test_main_installs_safe_docking_before_window_construction(self):
        from pathlib import Path

        root = Path(__file__).parents[1]
        main_source = (root / "lab_workspace" / "__main__.py").read_text(encoding="utf-8")
        docking_source = (root / "lab_workspace" / "ui" / "safe_docking.py").read_text(encoding="utf-8")

        self.assertIn("install_safe_tool_host(MainWindow)", main_source)
        self.assertIn("dock.setWidget(None)", docking_source)
        self.assertNotIn("dock.setParent(target.content)", docking_source)
        self.assertIn("content.setParent(target.content)", docking_source)


if __name__ == "__main__":
    unittest.main()
