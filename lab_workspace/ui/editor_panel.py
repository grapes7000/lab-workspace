from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton


class EditorPanel(QWidget):
    history_requested = Signal()
    checkpoint_requested = Signal()

    def __init__(self, title, placeholder, parent=None):
        super().__init__(parent)
        self.setObjectName("WorkPane")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        header_widget = QWidget()
        header_widget.setObjectName("PaneHeader")
        header = QHBoxLayout(header_widget)
        header.setContentsMargins(6, 3, 6, 3)
        header.setSpacing(1)
        label = QLabel(title); label.setObjectName("PanelTitle")
        self.counter = QLabel("0 words | 0 characters")
        history = QPushButton("History")
        checkpoint = QPushButton("Checkpoint")
        history.clicked.connect(self.history_requested)
        checkpoint.clicked.connect(self.checkpoint_requested)
        header.addWidget(label); header.addStretch(); header.addWidget(self.counter)
        header.addWidget(checkpoint); header.addWidget(history)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(placeholder)
        self.editor.setTabStopDistance(32)
        self.editor.textChanged.connect(self.update_count)
        layout.addWidget(header_widget); layout.addWidget(self.editor)

    def update_count(self):
        text = self.editor.toPlainText()
        self.counter.setText(f"{len(text.split()):,} words | {len(text):,} characters")
