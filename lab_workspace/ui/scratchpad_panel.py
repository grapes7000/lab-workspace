import difflib

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

from lab_workspace.ui.editor_panel import EditorPanel


class ScratchEditor(QPlainTextEdit):
    recover_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ghosts = []

    def set_ghosts(self, ghosts):
        self._ghosts = list(ghosts)
        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._ghosts:
            return
        painter = QPainter(self.viewport())
        color = QColor(self.palette().color(self.foregroundRole()))
        color.setAlpha(95)
        painter.setPen(color)
        metrics = painter.fontMetrics()
        document_length = len(self.toPlainText())
        for ghost in self._ghosts:
            cursor = QTextCursor(self.document())
            cursor.setPosition(min(max(0, ghost["position"]), document_length))
            rect = self.cursorRect(cursor)
            x, y = rect.left(), rect.top() + metrics.ascent()
            for line in ghost["fragment"].splitlines() or [""]:
                painter.drawText(x, y, line)
                y += metrics.height()
        painter.end()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Tab and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.recover_requested.emit()
            return
        super().keyPressEvent(event)


class ScratchpadPanel(EditorPanel):
    deletion_grouped = Signal(str, int)
    ghosts_overwritten = Signal(object)
    recover_requested = Signal()
    DELETION_GROUP_DELAY_MS = 750

    def __init__(self, title, placeholder, parent=None):
        super().__init__(title, placeholder, parent)
        old_editor = self.editor
        self.editor = ScratchEditor()
        self.editor.setPlaceholderText(placeholder)
        self.editor.setTabStopDistance(32)
        self.layout().replaceWidget(old_editor, self.editor)
        old_editor.hide()
        old_editor.deleteLater()
        self._previous_text = ""
        self._tracking = True
        self._ghosts = []
        self._pending_deletion = None
        self._deletion_timer = QTimer(self)
        self._deletion_timer.setSingleShot(True)
        self._deletion_timer.setInterval(self.DELETION_GROUP_DELAY_MS)
        self._deletion_timer.timeout.connect(self.flush_deletion_group)
        self.editor.textChanged.connect(self._text_changed)
        self.editor.textChanged.connect(self.update_count)
        self.editor.recover_requested.connect(self.recover_requested)

    def set_initial_text(self, text):
        self._tracking = False
        self.editor.setPlainText(text)
        self._previous_text = text
        self._tracking = True

    def set_ghosts(self, rows):
        self._ghosts = [
            {"id": int(row["id"]), "fragment": row["fragment"], "position": int(row["position"])}
            for row in rows
        ]
        self._refresh_ghosts()

    def _text_changed(self):
        current = self.editor.toPlainText()
        if self._tracking:
            matcher = difflib.SequenceMatcher(None, self._previous_text, current, autojunk=False)
            removed = []
            inserted = []
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag in ("delete", "replace") and i2 > i1:
                    removed.append((self._previous_text[i1:i2], i1))
                if tag in ("insert", "replace"):
                    inserted.append((i1, i2, j2 - j1))
            self._update_ghost_positions(removed, inserted)
            if removed:
                for fragment, position in removed:
                    self._queue_deletion(fragment, position)
        self._previous_text = current

    def _queue_deletion(self, fragment, position):
        if not fragment:
            return
        pending = self._pending_deletion
        if pending is None:
            self._pending_deletion = {"fragment": fragment, "position": position}
        elif position == pending["position"]:
            pending["fragment"] += fragment
        elif position + len(fragment) == pending["position"]:
            pending["fragment"] = fragment + pending["fragment"]
            pending["position"] = position
        else:
            self.flush_deletion_group()
            self._pending_deletion = {"fragment": fragment, "position": position}
        self._deletion_timer.start()
        self._refresh_ghosts()

    def flush_deletion_group(self):
        if self._pending_deletion is None:
            return
        pending = self._pending_deletion
        self._pending_deletion = None
        self._deletion_timer.stop()
        self.deletion_grouped.emit(pending["fragment"], pending["position"])

    def commit_ghost(self, fragment_id, fragment, position):
        self._ghosts.append({"id": int(fragment_id), "fragment": fragment, "position": position})
        self._refresh_ghosts()

    def latest_ghost(self):
        self.flush_deletion_group()
        return max(self._ghosts, key=lambda ghost: ghost["id"], default=None)

    def remove_ghost(self, fragment_id):
        self._ghosts = [ghost for ghost in self._ghosts if ghost["id"] != int(fragment_id)]
        self._refresh_ghosts()

    def _update_ghost_positions(self, removed, inserted):
        # An insertion at a ghost anchor replaces its visual placeholder.  A
        # replacement range or deletion across an anchor resolves it as well.
        invalidated = set()
        for start, end, _length in inserted:
            invalidated.update(
                ghost["id"] for ghost in self._ghosts
                if start <= ghost["position"] <= max(start, end)
            )
        removed_ranges = [(position, position + len(fragment)) for fragment, position in removed]
        invalidated.update(
            ghost["id"] for ghost in self._ghosts
            if any(start < ghost["position"] < end for start, end in removed_ranges)
        )
        self._ghosts = [ghost for ghost in self._ghosts if ghost["id"] not in invalidated]
        if invalidated:
            self.ghosts_overwritten.emit(sorted(invalidated))
        for start, end in removed_ranges:
            for ghost in self._ghosts:
                if ghost["position"] >= end:
                    ghost["position"] -= end - start
        for start, end, length in inserted:
            delta = length - (end - start)
            for ghost in self._ghosts:
                if ghost["position"] > end:
                    ghost["position"] += delta
        self._refresh_ghosts()

    def _refresh_ghosts(self):
        ghosts = list(self._ghosts)
        if self._pending_deletion is not None:
            ghosts.append({"id": -1, **self._pending_deletion})
        self.editor.set_ghosts(sorted(ghosts, key=lambda ghost: ghost["position"]))

    def insert_recovered(self, fragment, position):
        self._tracking = False
        cursor = self.editor.textCursor()
        cursor.setPosition(min(max(0, position), len(self.editor.toPlainText())))
        cursor.insertText(fragment)
        self.editor.setTextCursor(cursor)
        self._previous_text = self.editor.toPlainText()
        self._tracking = True
        self.update_count()
