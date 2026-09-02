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
        for name in ("markdown-it.min.js", "katex.min.js", "mhchem.min.js", "highlight.min.js", "mermaid.min.js"):
            self.assertTrue((ASSET_DIR / name).is_file())
        self.assertLess(
            html.index("mhchem.min.js"),
            html.index("katex-auto-render.min.js"),
        )

    def test_preview_contains_safe_obsidian_style_rendering(self):
        html = RichMarkdownPreview.html_for_markdown(
            "> [!WARNING] Careful\n> Details\n\n==highlight== [[Note|Shown]] ![[file.png]] #lab"
        )
        for marker in (
            "installCallouts", "callout-warning", "replaceObsidianSyntax",
            "wiki-link", "obsidian-embed", "markdown-tag",
        ):
            self.assertIn(marker, html)
        self.assertIn("html:false", html)

    def test_markdown_menu_includes_obsidian_focused_templates(self):
        keys = {key for _label, key in MarkdownPanel.INSERT_ITEMS}
        self.assertTrue({"callout", "wiki_link", "embed", "highlight", "tag"} <= keys)


if __name__ == "__main__":
    unittest.main()
