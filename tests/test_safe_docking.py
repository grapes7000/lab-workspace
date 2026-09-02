import unittest


class SafeDockingDesignTests(unittest.TestCase):
    def test_docks_keep_a_permanent_host_while_only_tool_content_moves(self):
        from pathlib import Path

        root = Path(__file__).parents[1]
        main_source = (root / "lab_workspace" / "ui" / "main_window.py").read_text(encoding="utf-8")
        docking_source = (root / "lab_workspace" / "ui" / "safe_docking.py").read_text(encoding="utf-8")

        self.assertIn("class ToolHost(QWidget)", docking_source)
        self.assertIn("dock.setWidget(host)", main_source)
        self.assertLess(
            main_source.index("tool.setParent(None)"),
            main_source.index("dock.setWidget(host)"),
        )
        self.assertIn("self.tool_hosts[key].take_tool()", main_source)
        self.assertIn("self.tool_hosts[key].set_tool(content)", main_source)
        self.assertNotIn("dock.setParent(target.content)", main_source)
        self.assertNotIn("dock.setWidget(None)", docking_source)


if __name__ == "__main__":
    unittest.main()
