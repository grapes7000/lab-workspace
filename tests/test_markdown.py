import unittest
from pathlib import Path

from lab_workspace.ui.markdown_panel import MarkdownPanel


class MarkdownTests(unittest.TestCase):
    def test_saved_document_uses_relative_image_reference(self):
        image = Path("/tmp/report/images/chart.png")
        document = Path("/tmp/report/note.md")
        self.assertEqual(MarkdownPanel.image_markdown(image, document), "![chart](images/chart.png)")

    def test_unsaved_document_uses_file_url(self):
        image = Path("/tmp/diagram.png")
        self.assertEqual(MarkdownPanel.image_markdown(image), "![diagram](file:///tmp/diagram.png)")


if __name__ == "__main__":
    unittest.main()
