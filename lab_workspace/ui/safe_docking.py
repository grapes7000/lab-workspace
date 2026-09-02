from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget


def install_safe_tool_host(main_window_class):
    """Install safe tool movement methods on MainWindow.

    QDockWidget is a QMainWindow wrapper and should not itself be embedded in the
    center layout. Only its content widget moves between the dock wrapper and a
    CenterPane. This keeps Qt ownership/layout bookkeeping consistent and avoids
    native crashes from giving one QDockWidget two incompatible roles.
    """

    def register_tool_dock(self, key, dock, area):
        if not hasattr(self, "tool_widgets"):
            self.tool_widgets = {}
        content = dock.widget()
        if content is None:
            raise RuntimeError(f"Tool dock {key!r} has no content widget")
        self.tool_docks[key] = dock
        self.tool_widgets[key] = content
        self.tool_last_areas[key] = area
        self.addDockWidget(area, dock)
        dock.dockLocationChanged.connect(
            lambda new_area, tool_key=key: self.remember_tool_area(tool_key, new_area)
        )

    def release_dock_content(self, key):
        dock = self.tool_docks[key]
        content = self.tool_widgets[key]
        dock.hide()
        area = self.dockWidgetArea(dock)
        if area != Qt.DockWidgetArea.NoDockWidgetArea:
            self.remember_tool_area(key, area)
        self.removeDockWidget(dock)
        if dock.isFloating():
            dock.setFloating(False)

        # Detach the actual tool widget. Never reparent the QDockWidget itself.
        content.setParent(None)
        try:
            dock.setWidget(None)
        except TypeError:
            # Older bindings may reject None despite the C++ API taking a
            # QWidget pointer. A tiny placeholder keeps the wrapper valid.
            placeholder = QWidget(dock)
            placeholder.setObjectName("DetachedToolPlaceholder")
            dock.setWidget(placeholder)
        return content

    def move_tool_to_center(self, key, slot=0):
        if key not in self.tool_docks:
            return
        slot = 0 if slot not in (0, 1) else slot
        if slot == 1 and not self.center_host.split_button.isChecked():
            self.center_host.set_split_enabled(True)

        current_slot = self.center_slot_for_tool(key)
        if current_slot == slot:
            content = self.tool_widgets[key]
            content.show()
            content.setFocus(Qt.FocusReason.OtherFocusReason)
            return

        if current_slot is not None:
            content = self.center_host.pane(current_slot).detach()
            if content is None:
                content = self.tool_widgets[key]
        else:
            content = release_dock_content(self, key)

        target = self.center_host.pane(slot)
        if target.current_key is not None and target.current_key != key:
            self.move_center_tool_to_dock(slot, show=False)

        content.setParent(target.content)
        target.attach(key, self.TOOL_TITLES[key], content)
        content.show()
        self.settings.setValue(f"center/tool{slot}", key)

    def move_center_tool_to_dock(self, slot, show=False):
        pane = self.center_host.pane(slot)
        key = pane.current_key
        if key is None:
            return
        content = pane.detach()
        if content is None:
            return

        dock = self.tool_docks[key]
        content.setParent(None)
        dock.setParent(self)
        dock.setWidget(content)
        area = self.tool_last_areas.get(key, self.TOOL_DEFAULT_AREAS[key])
        self.addDockWidget(area, dock)
        if show:
            dock.show()
            dock.raise_()
        else:
            dock.hide()
        self.settings.remove(f"center/tool{slot}")

    def toggle_tool(self, key):
        slot = self.center_slot_for_tool(key)
        if slot is not None:
            content = self.tool_widgets[key]
            content.show()
            content.setFocus(Qt.FocusReason.OtherFocusReason)
            return

        dock = self.tool_docks[key]
        if dock.isVisible():
            dock.hide()
            return
        if self.dockWidgetArea(dock) == Qt.DockWidgetArea.NoDockWidgetArea:
            dock.setParent(self)
            dock.setWidget(self.tool_widgets[key])
            self.addDockWidget(
                self.tool_last_areas.get(key, self.TOOL_DEFAULT_AREAS[key]), dock
            )
        dock.show()
        dock.raise_()

    main_window_class.register_tool_dock = register_tool_dock
    main_window_class.move_tool_to_center = move_tool_to_center
    main_window_class.move_center_tool_to_dock = move_center_tool_to_dock
    main_window_class.toggle_tool = toggle_tool
    return main_window_class
