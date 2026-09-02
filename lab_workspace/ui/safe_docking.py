"""Stable Qt containers used by the workspace shell.

Only the actual tool view moves between a center pane and this host.  The host
is permanently installed in its QDockWidget, so QMainWindow never has to track
a dock widget that has been reparented into a normal layout.
"""

from PySide6.QtWidgets import QVBoxLayout, QWidget


class ToolHost(QWidget):
    """The permanent content widget of a QDockWidget."""

    def __init__(self, tool, parent=None):
        super().__init__(parent)
        self._tool = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.set_tool(tool)

    def take_tool(self):
        tool = self._tool
        if tool is not None:
            self._layout.removeWidget(tool)
        self._tool = None
        return tool

    def set_tool(self, tool):
        if tool is self._tool:
            return
        self.take_tool()
        self._tool = tool
        if tool is not None:
            self._layout.addWidget(tool)
