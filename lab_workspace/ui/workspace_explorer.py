from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


ROLE_KIND = Qt.ItemDataRole.UserRole
ROLE_ID = Qt.ItemDataRole.UserRole + 1
ROLE_DOCUMENT = Qt.ItemDataRole.UserRole + 2


class WorkspaceExplorer(QWidget):
    workspace_requested = Signal(int)
    document_requested = Signal(int, str)
    new_requested = Signal()
    rename_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_workspace_id = None
        self.setObjectName("WorkspaceExplorer")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        header = QHBoxLayout()
        title = QLabel("WORKSPACES")
        title.setObjectName("ExplorerTitle")
        new_button = QPushButton("+")
        new_button.setFixedWidth(30)
        new_button.setToolTip("New workspace")
        rename_button = QPushButton("Rename")
        rename_button.setToolTip("Rename selected workspace")
        new_button.clicked.connect(self.new_requested)
        rename_button.clicked.connect(self._rename_selected)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(new_button)
        header.addWidget(rename_button)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.itemActivated.connect(self._activate)

        hint = QLabel("Double-click a workspace or document to open it.")
        hint.setWordWrap(True)
        hint.setObjectName("ExplorerHint")

        layout.addLayout(header)
        layout.addWidget(self.tree, 1)
        layout.addWidget(hint)

    def set_workspaces(self, rows, active_workspace_id=None):
        self.active_workspace_id = active_workspace_id
        self.tree.clear()
        active_item = None
        for row in rows:
            workspace_id = int(row["id"])
            item = QTreeWidgetItem([row["name"]])
            item.setData(0, ROLE_KIND, "workspace")
            item.setData(0, ROLE_ID, workspace_id)
            if workspace_id == active_workspace_id:
                font = QFont(item.font(0))
                font.setBold(True)
                item.setFont(0, font)
                active_item = item
            for kind, label in (("scratchpad", "Scratchpad"), ("final", "Final Document")):
                child = QTreeWidgetItem([label])
                child.setData(0, ROLE_KIND, "document")
                child.setData(0, ROLE_ID, workspace_id)
                child.setData(0, ROLE_DOCUMENT, kind)
                item.addChild(child)
            self.tree.addTopLevelItem(item)
        if active_item is not None:
            active_item.setExpanded(True)
            self.tree.setCurrentItem(active_item)

    def selected_workspace_id(self):
        item = self.tree.currentItem()
        if item is None:
            return self.active_workspace_id
        workspace_id = item.data(0, ROLE_ID)
        return int(workspace_id) if workspace_id is not None else self.active_workspace_id

    def _activate(self, item, _column=0):
        workspace_id = item.data(0, ROLE_ID)
        if workspace_id is None:
            return
        workspace_id = int(workspace_id)
        if item.data(0, ROLE_KIND) == "document":
            self.document_requested.emit(workspace_id, item.data(0, ROLE_DOCUMENT))
        else:
            self.workspace_requested.emit(workspace_id)

    def _rename_selected(self):
        workspace_id = self.selected_workspace_id()
        if workspace_id is not None:
            self.rename_requested.emit(int(workspace_id))
