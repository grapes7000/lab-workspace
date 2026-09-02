import unittest
from pathlib import Path

from lab_workspace.ui.markdown_panel import MarkdownPanel
from lab_workspace.ui.rich_markdown_preview import ASSET_DIR, RichMarkdownPreview


class MarkdownTests(unittest.TestCase):
    def test_saved_document_uses_relative_image_reference(self):
        image = Path("/tmp/report/images/chart.png")
        document = Path("/tmp/report/note.md")
        self.assertEqual(MarkdownPanel.image_markdown(image, document), "![chart](images/chart.png)")

    def test_unsaved_document_uses_file_url(self):
        image = Path("/tmp/diagram.png")
        self.assertEqual(MarkdownPanel.image_markdown(image), "![diagram](file:///tmp/diagram.png)")

    def test_rich_preview_escapes_raw_html_and_loads_offline_assets(self):
        html = RichMarkdownPreview.html_for_markdown("<script>alert(1)</script>\n\n$x^2$")
        self.assertIn("html:false", html)
        self.assertIn("\\u003cscript", html)
        self.assertNotIn("https://", html)
        for name in ("markdown-it.min.js", "katex.min.js", "highlight.min.js", "mermaid.min.js"):
            self.assertTrue((ASSET_DIR / name).is_file())


if __name__ == "__main__":
    unittest.main()
