from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSplitter, QStackedWidget, QTextBrowser, QVBoxLayout, QWidget


class MarkdownPanel(QWidget):
    history_requested = Signal()
    checkpoint_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        header = QHBoxLayout()
        header.setSpacing(1)
        title = QLabel("Final Document")
        title.setObjectName("PanelTitle")
        self.counter = QLabel("0 words | 0 characters")
        self.edit_button = QPushButton("Edit")
        self.preview_button = QPushButton("Preview")
        self.split_button = QPushButton("Side by Side")
        checkpoint = QPushButton("Checkpoint")
        history = QPushButton("History")
        checkpoint.clicked.connect(self.checkpoint_requested)
        history.clicked.connect(self.history_requested)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.counter)
        for widget in (self.edit_button, self.preview_button, self.split_button, checkpoint, history):
            header.addWidget(widget)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Write Markdown here.")
        self.editor.setTabStopDistance(32)
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.split_editor = QPlainTextEdit()
        self.split_editor.setPlaceholderText("Write Markdown here.")
        self.split_editor.setTabStopDistance(32)
        self.split_preview = QTextBrowser()
        self.split_preview.setOpenExternalLinks(True)
        self.splitter.addWidget(self.split_editor)
        self.splitter.addWidget(self.split_preview)
        self.splitter.setSizes([600, 600])
        self.stack = QStackedWidget()
        self.stack.addWidget(self.editor)
        self.stack.addWidget(self.preview)
        self.stack.addWidget(self.splitter)
        layout.addLayout(header)
        layout.addWidget(self.stack)
        self._syncing = False
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

    def text(self):
        return self.editor.toPlainText()

    def set_mode(self, index):
        if index in (1, 2):
            self.update_preview()
        self.stack.setCurrentIndex(index)
        for button_index, button in enumerate((self.edit_button, self.preview_button, self.split_button)):
            button.setEnabled(button_index != index)

    def update_preview(self):
        self.preview.setMarkdown(self.text())
        self.split_preview.setMarkdown(self.text())
