import os
from pathlib import Path
from urllib.parse import quote

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QPlainTextEdit, QPushButton, QSplitter, QStackedWidget, QToolButton, QVBoxLayout, QWidget
from lab_workspace.ui.rich_markdown_preview import RichMarkdownPreview


class MarkdownPanel(QWidget):
    history_requested = Signal()
    checkpoint_requested = Signal()

    INSERT_ITEMS = (
        ("Heading 1", "heading_1"), ("Heading 2", "heading_2"), ("Heading 3", "heading_3"),
        ("Bold", "bold"), ("Italic", "italic"), ("Strikethrough", "strike"),
        ("Highlight", "highlight"), ("Inline Code", "inline_code"), ("Code Block", "code_block"),
        ("Link", "link"), ("Image", "image"), ("Bulleted List", "bullet_list"),
        ("Numbered List", "numbered_list"), ("Task Checkbox", "task"), ("Table", "table"),
        ("Quote", "quote"), ("Divider", "divider"), ("Callout", "callout"),
        ("Wiki Link", "wiki_link"), ("Embed", "embed"), ("Tag", "tag"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WorkPane")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        header_widget = QWidget()
        header_widget.setObjectName("PaneHeader")
        header = QHBoxLayout(header_widget)
        header.setContentsMargins(6, 3, 6, 3)
        header.setSpacing(1)
        title = QLabel("Final Document")
        title.setObjectName("PanelTitle")
        self.counter = QLabel("0 words | 0 characters")
        self.edit_button = QPushButton("Edit")
        self.preview_button = QPushButton("Preview")
        self.split_button = QPushButton("Side by Side")
        self.markdown_button = QToolButton()
        self.markdown_button.setText("Markdown")
        self.markdown_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.markdown_menu = QMenu(self.markdown_button)
        self.markdown_button.setMenu(self.markdown_menu)
        self._build_markdown_menu()
        checkpoint = QPushButton("Checkpoint")
        history = QPushButton("History")
        checkpoint.clicked.connect(self.checkpoint_requested)
        history.clicked.connect(self.history_requested)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.counter)
        for widget in (self.edit_button, self.preview_button, self.split_button, self.markdown_button, checkpoint, history):
            header.addWidget(widget)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Write Markdown here.")
        self.editor.setTabStopDistance(32)
        # QWebEngine starts a Chromium process as soon as a view is created.
        # Keep it out of the startup path: a broken graphics/WebEngine setup
        # should not prevent the editor and the rest of the workspace opening.
        self.preview = None
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.split_editor = QPlainTextEdit()
        self.split_editor.setPlaceholderText("Write Markdown here.")
        self.split_editor.setTabStopDistance(32)
        self.split_preview = None
        self.splitter.addWidget(self.split_editor)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.editor)
        layout.addWidget(header_widget)
        layout.addWidget(self.stack)
        self._syncing = False
        self.document_path = None
        self.editor.textChanged.connect(lambda: self.sync_from(self.editor))
        self.split_editor.textChanged.connect(lambda: self.sync_from(self.split_editor))
        self.edit_button.clicked.connect(lambda: self.set_mode(0))
        self.preview_button.clicked.connect(lambda: self.set_mode(1))
        self.split_button.clicked.connect(lambda: self.set_mode(2))
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(300)
        self.preview_timer.timeout.connect(self.update_preview)
        self.set_mode(0)

    def sync_from(self, source):
        if self._syncing:
            return
        self._syncing = True
        text = source.toPlainText()
        target = self.split_editor if source is self.editor else self.editor
        cursor_position = target.textCursor().position()
        target.setPlainText(text)
        cursor = target.textCursor()
        cursor.setPosition(min(cursor_position, len(text)))
        target.setTextCursor(cursor)
        self._syncing = False
        self.counter.setText(f"{len(text.split()):,} words | {len(text):,} characters")
        self.preview_timer.start()

    def set_text(self, text):
        self._syncing = True
        self.editor.setPlainText(text)
        self.split_editor.setPlainText(text)
        self._syncing = False
        self.counter.setText(f"{len(text.split()):,} words | {len(text):,} characters")
        self.update_preview()

    def set_document_path(self, path):
        self.document_path = Path(path) if path else None
        if self.preview is not None:
            self.preview.set_document_path(self.document_path)
            self.split_preview.set_document_path(self.document_path)

    @staticmethod
    def image_markdown(path, document_path=None):
        image_path = Path(path)
        if document_path:
            reference = quote(os.path.relpath(image_path, Path(document_path).parent).replace(os.sep, "/"))
        else:
            reference = QUrl.fromLocalFile(str(image_path)).toString(QUrl.ComponentFormattingOption.FullyEncoded)
        return f"![{image_path.stem}]({reference})"

    def insert_markdown(self, text):
        editor = self.split_editor if self.split_editor.hasFocus() else self.editor
        cursor = editor.textCursor()
        cursor.insertText(text)
        editor.setTextCursor(cursor)

    def _build_markdown_menu(self):
        groups = (
            ("Text", ("heading_1", "heading_2", "heading_3", "bold", "italic", "strike", "highlight", "inline_code")),
            ("Blocks", ("code_block", "quote", "divider", "callout")),
            ("Lists & tables", ("bullet_list", "numbered_list", "task", "table")),
            ("Links & Obsidian", ("link", "image", "wiki_link", "embed", "tag")),
        )
        labels = dict((key, label) for label, key in self.INSERT_ITEMS)
        for group, keys in groups:
            submenu = self.markdown_menu.addMenu(group)
            for key in keys:
                submenu.addAction(labels[key], lambda checked=False, template=key: self.insert_template(template))

    def insert_template(self, template):
        editor = self.split_editor if self.split_editor.hasFocus() else self.editor
        cursor = editor.textCursor()
        selected = cursor.selectedText().replace("\u2029", "\n")
        inline = {
            "bold": ("**", "**", "bold text"),
            "italic": ("*", "*", "italic text"),
            "strike": ("~~", "~~", "struck text"),
            "highlight": ("==", "==", "highlighted text"),
            "inline_code": ("`", "`", "code"),
            "link": ("[", "](url)", "link text"),
            "wiki_link": ("[[", "]]", "Note name"),
        }
        blocks = {
            "heading_1": "# Heading\n",
            "heading_2": "## Heading\n",
            "heading_3": "### Heading\n",
            "code_block": "```text\n\n```\n",
            "image": "![alt text](path/to/image.png)\n",
            "bullet_list": "- List item\n",
            "numbered_list": "1. List item\n",
            "task": "- [ ] Task\n",
            "table": "| Column 1 | Column 2 |\n| --- | --- |\n|  |  |\n",
            "quote": "> Quote\n",
            "divider": "\n---\n",
            "callout": "> [!NOTE]\n> Callout text\n",
            "embed": "![[attachment.png]]\n",
            "tag": "#tag",
        }
        if template in inline:
            prefix, suffix, fallback = inline[template]
            cursor.insertText(f"{prefix}{selected or fallback}{suffix}")
        else:
            cursor.insertText(blocks[template])
        editor.setTextCursor(cursor)

    def insert_image(self, path):
        self.insert_markdown(self.image_markdown(path, self.document_path))

    def text(self):
        return self.editor.toPlainText()

    def set_mode(self, index):
        if index in (1, 2):
            self.ensure_previews()
            self.update_preview()
        self.stack.setCurrentIndex(index)
        for button_index, button in enumerate((self.edit_button, self.preview_button, self.split_button)):
            button.setEnabled(button_index != index)

    def update_preview(self):
        if self.preview is None:
            return
        self.preview.set_markdown(self.text(), self.document_path)
        self.split_preview.set_markdown(self.text(), self.document_path)

    def ensure_previews(self):
        if self.preview is not None:
            return
        self.preview = RichMarkdownPreview()
        self.split_preview = RichMarkdownPreview()
        self.preview.set_document_path(self.document_path)
        self.split_preview.set_document_path(self.document_path)
        self.splitter.addWidget(self.split_preview)
        self.splitter.setSizes([600, 600])
        self.stack.addWidget(self.preview)
        self.stack.addWidget(self.splitter)
