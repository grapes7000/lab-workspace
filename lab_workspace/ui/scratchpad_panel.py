import difflib
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QLabel
from lab_workspace.ui.editor_panel import EditorPanel


class ScratchEditor(QPlainTextEdit):
    recover_requested = Signal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Tab and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.recover_requested.emit()
            return
        super().keyPressEvent(event)


class ScratchpadPanel(EditorPanel):
    deletion_detected = Signal(str, int)
    recover_requested = Signal()

    def __init__(self, title, placeholder, parent=None):
        super().__init__(title, placeholder, parent)
        old_editor = self.editor
        self.editor = ScratchEditor()
        self.editor.setPlaceholderText(placeholder)
        self.editor.setTabStopDistance(32)
        self.layout().replaceWidget(old_editor, self.editor)
        old_editor.deleteLater()
        self.ghost = QLabel("Deleted text will appear here. Press Tab in the scratchpad to recover it.")
        self.ghost.setObjectName("GhostText")
        self.ghost.setWordWrap(True)
        self.layout().addWidget(self.ghost)
        self._previous_text = ""
        self._tracking = True
        self.editor.textChanged.connect(self._text_changed)
        self.editor.textChanged.connect(self.update_count)
        self.editor.recover_requested.connect(self.recover_requested)

    def set_initial_text(self, text):
        self._tracking = False
        self.editor.setPlainText(text)
        self._previous_text = text
        self._tracking = True

    def _text_changed(self):
        current = self.editor.toPlainText()
        if self._tracking:
            matcher = difflib.SequenceMatcher(None, self._previous_text, current, autojunk=False)
            removed = []
            for tag, i1, i2, _j1, _j2 in matcher.get_opcodes():
                if tag in ("delete", "replace") and i2 > i1:
                    removed.append((self._previous_text[i1:i2], i1))
            if removed:
                fragment, position = max(removed, key=lambda item: len(item[0]))
                self.deletion_detected.emit(fragment, position)
        self._previous_text = current

    def set_ghost(self, fragment):
        display = fragment.replace("\n", " ↵ ")
        self.ghost.setText(f"Deleted, preserved in history: {display}    [Tab to recover]")

    def clear_ghost(self):
        self.ghost.setText("No unrecovered deletion. All prior scratchpad states remain in History.")

    def insert_recovered(self, fragment, position):
        self._tracking = False
        cursor = self.editor.textCursor()
        position = min(max(0, position), len(self.editor.toPlainText()))
        cursor.setPosition(position)
        cursor.insertText(fragment)
        self.editor.setTextCursor(cursor)
        self._previous_text = self.editor.toPlainText()
        self._tracking = True
        self.update_count()
