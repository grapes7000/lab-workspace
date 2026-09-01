import difflib
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPlainTextEdit, QPushButton, QLabel


class HistoryDialog(QDialog):
    restore_requested = Signal(int)

    def __init__(self, database, key, current_text, parent=None):
        super().__init__(parent)
        self.database, self.key, self.current_text = database, key, current_text
        self.setWindowTitle("Revision History")
        self.resize(900, 620)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select a revision to compare with the current text."))
        row = QHBoxLayout(); self.list = QListWidget(); self.diff = QPlainTextEdit(); self.diff.setReadOnly(True)
        row.addWidget(self.list, 1); row.addWidget(self.diff, 3); layout.addLayout(row)
        buttons = QHBoxLayout(); buttons.addStretch(); restore = QPushButton("Restore Selected")
        close = QPushButton("Close"); buttons.addWidget(restore); buttons.addWidget(close); layout.addLayout(buttons)
        self.rows = self.database.revisions(key)
        for item in self.rows:
            self.list.addItem(f"#{item['id']}  {item['created_at']}  {item['reason']}")
        self.list.currentRowChanged.connect(self.show_diff)
        restore.clicked.connect(self.restore); close.clicked.connect(self.accept)
        if self.rows: self.list.setCurrentRow(0)

    def show_diff(self, index):
        if index < 0: return
        old = self.rows[index]["text"].splitlines()
        new = self.current_text.splitlines()
        lines = list(difflib.ndiff(old, new))
        self.diff.clear(); cursor = self.diff.textCursor()
        formats = {"- ": QColor("#b36b6b"), "+ ": QColor("#72b879"), "? ": QColor("#888888")}
        for line in lines:
            fmt = QTextCharFormat(); fmt.setForeground(formats.get(line[:2], self.diff.palette().text().color()))
            if line.startswith("- "): fmt.setFontStrikeOut(True)
            cursor.insertText(line + "\n", fmt)
        self.diff.setTextCursor(cursor)

    def restore(self):
        index = self.list.currentRow()
        if index >= 0:
            self.restore_requested.emit(int(self.rows[index]["id"]))
            self.accept()
