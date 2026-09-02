from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class CenterPane(QWidget):
    tool_requested = Signal(int, object)
    dock_requested = Signal(int)
    close_requested = Signal(int)

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.current_key = None
        self.current_widget = None
        self._updating = False
        self.setObjectName("CenterPane")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("CenterPaneHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(6, 4, 6, 4)
        header_layout.setSpacing(5)

        self.label = QLabel("Main")
        self.label.setObjectName("CenterPaneLabel")
        self.selector = QComboBox()
        self.selector.setMinimumWidth(160)
        self.selector.currentIndexChanged.connect(self._selection_changed)
        self.dock_button = QPushButton("Dock")
        self.dock_button.setToolTip("Return this tool to a dockable side window")
        self.dock_button.clicked.connect(lambda: self.dock_requested.emit(self.index))
        self.close_button = QPushButton("×")
        self.close_button.setFixedWidth(30)
        self.close_button.setToolTip("Close this center pane")
        self.close_button.clicked.connect(lambda: self.close_requested.emit(self.index))

        header_layout.addWidget(self.label)
        header_layout.addWidget(self.selector, 1)
        header_layout.addWidget(self.dock_button)
        header_layout.addWidget(self.close_button)

        self.content = QWidget()
        self.content.setObjectName("CenterPaneContent")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.empty = QLabel("Choose a tool for this main pane.")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setObjectName("CenterPaneEmpty")
        self.content_layout.addWidget(self.empty)

        layout.addWidget(header)
        layout.addWidget(self.content, 1)
        self._update_controls()

    def set_choices(self, tools):
        selected = self.current_key
        self._updating = True
        self.selector.clear()
        self.selector.addItem("Empty", None)
        for key, title in tools:
            self.selector.addItem(title, key)
        index = self.selector.findData(selected)
        self.selector.setCurrentIndex(index if index >= 0 else 0)
        self._updating = False

    def _selection_changed(self):
        if self._updating:
            return
        self.tool_requested.emit(self.index, self.selector.currentData())

    def attach(self, key, title, widget):
        if self.current_widget is widget and self.current_key == key:
            return
        self.detach()
        self.current_key = key
        self.current_widget = widget
        self.empty.hide()
        self.content_layout.addWidget(widget)
        widget.show()
        self.label.setText("Main" if self.index == 0 else "Split")
        self._updating = True
        idx = self.selector.findData(key)
        if idx >= 0:
            self.selector.setCurrentIndex(idx)
        self._updating = False
        self._update_controls()

    def detach(self):
        widget = self.current_widget
        if widget is not None:
            self.content_layout.removeWidget(widget)
        self.current_widget = None
        self.current_key = None
        self.empty.show()
        self._updating = True
        idx = self.selector.findData(None)
        if idx >= 0:
            self.selector.setCurrentIndex(idx)
        self._updating = False
        self._update_controls()
        return widget

    def _update_controls(self):
        has_tool = self.current_key is not None
        self.dock_button.setEnabled(has_tool)
        self.close_button.setEnabled(has_tool or self.index == 1)


class CenterHost(QWidget):
    tool_requested = Signal(int, object)
    dock_requested = Signal(int)
    close_requested = Signal(int)
    split_toggled = Signal(bool)
    orientation_toggled = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CenterHost")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        controls = QWidget()
        controls.setObjectName("CenterControls")
        control_layout = QHBoxLayout(controls)
        control_layout.setContentsMargins(6, 4, 6, 4)
        control_layout.setSpacing(5)
        title = QLabel("WORK AREA")
        title.setObjectName("CenterControlsTitle")
        self.split_button = QPushButton("Split")
        self.split_button.setCheckable(True)
        self.split_button.setToolTip("Show a second main pane")
        self.split_button.toggled.connect(self._split_changed)
        self.orientation_button = QPushButton("Side by Side")
        self.orientation_button.setToolTip("Toggle side-by-side / top-and-bottom center split")
        self.orientation_button.clicked.connect(self.toggle_orientation)
        control_layout.addWidget(title)
        control_layout.addStretch()
        control_layout.addWidget(self.split_button)
        control_layout.addWidget(self.orientation_button)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.panes = [CenterPane(0), CenterPane(1)]
        for pane in self.panes:
            self.splitter.addWidget(pane)
            pane.tool_requested.connect(self.tool_requested)
            pane.dock_requested.connect(self.dock_requested)
            pane.close_requested.connect(self.close_requested)
        self.panes[1].hide()
        self.splitter.setSizes([1000, 0])

        layout.addWidget(controls)
        layout.addWidget(self.splitter, 1)

    def set_tools(self, tools):
        choices = list(tools)
        for pane in self.panes:
            pane.set_choices(choices)

    def _split_changed(self, enabled):
        self.panes[1].setVisible(enabled)
        if enabled:
            self.splitter.setSizes([700, 700])
        self.split_toggled.emit(enabled)

    def set_split_enabled(self, enabled, emit=False):
        self.split_button.blockSignals(not emit)
        self.split_button.setChecked(bool(enabled))
        self.split_button.blockSignals(False)
        self.panes[1].setVisible(bool(enabled))
        if enabled:
            self.splitter.setSizes([700, 700])

    def toggle_orientation(self):
        new_orientation = (
            Qt.Orientation.Vertical
            if self.splitter.orientation() == Qt.Orientation.Horizontal
            else Qt.Orientation.Horizontal
        )
        self.set_orientation(new_orientation)
        self.orientation_toggled.emit(int(new_orientation.value))

    def set_orientation(self, orientation):
        orientation = Qt.Orientation(orientation)
        self.splitter.setOrientation(orientation)
        self.orientation_button.setText(
            "Top / Bottom" if orientation == Qt.Orientation.Horizontal else "Side by Side"
        )

    def pane(self, index):
        return self.panes[index]
