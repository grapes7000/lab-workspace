from pathlib import Path

from PySide6.QtCore import QSize, Qt, QSettings, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStyle,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from lab_workspace.core.config import EXPORT_DIR
from lab_workspace.ui.calculator_dock import CalculatorDock
from lab_workspace.ui.history_dialog import HistoryDialog
from lab_workspace.ui.library import LibraryPage
from lab_workspace.ui.markdown_panel import MarkdownPanel
from lab_workspace.ui.scratchpad_panel import ScratchpadPanel
from lab_workspace.ui.stoichiometry import StoichiometryPage
from lab_workspace.ui.theme import apply_theme
from lab_workspace.ui.workspace_explorer import WorkspaceExplorer
from lab_workspace.ui.workspace_shell import CenterHost
from lab_workspace.ui.safe_docking import ToolHost


class MainWindow(QMainWindow):
    LAYOUT_STATE_VERSION = 2
    TOOL_TITLES = {
        "writing": "Writing",
        "calculator": "Science Calculator",
        "library": "Materials & Samples",
        "stoichiometry": "Stoichiometry",
    }

    TOOL_DEFAULT_AREAS = {
        "writing": Qt.DockWidgetArea.RightDockWidgetArea,
        "calculator": Qt.DockWidgetArea.LeftDockWidgetArea,
        "library": Qt.DockWidgetArea.RightDockWidgetArea,
        "stoichiometry": Qt.DockWidgetArea.RightDockWidgetArea,
    }

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.settings = QSettings()
        self.current_file = None
        self.current_workspace_id = None
        self.loading = False
        self.tool_docks = {}
        self.tool_hosts = {}
        self.tool_widgets = {}
        self.tool_last_areas = dict(self.TOOL_DEFAULT_AREAS)

        self.setWindowTitle("Lab Workspace")
        self.resize(1500, 900)
        self.setDockOptions(
            QMainWindow.DockOption.AnimatedDocks
            | QMainWindow.DockOption.AllowNestedDocks
            | QMainWindow.DockOption.AllowTabbedDocks
            | QMainWindow.DockOption.GroupedDragging
        )
        apply_theme(QApplication.instance(), self.settings.value("theme", "light"))

        self.build_writing_tool()
        self.center_host = CenterHost(self)
        self.setCentralWidget(self.center_host)

        self.build_tool_docks()
        self.build_workspace_explorer()
        self.center_host.set_tools(self.TOOL_TITLES.items())
        self.center_host.tool_requested.connect(self.center_tool_requested)
        self.center_host.dock_requested.connect(self.center_dock_requested)
        self.center_host.close_requested.connect(self.center_close_requested)
        self.center_host.split_toggled.connect(self.center_split_toggled)
        self.center_host.orientation_toggled.connect(self.center_orientation_changed)

        self.build_actions()
        self.build_menus()
        self.build_toolbar()
        self.build_activity_rail()
        self.connect_editors()

        self.autosave = QTimer(self)
        self.autosave.setSingleShot(True)
        self.autosave.setInterval(1200)
        self.autosave.timeout.connect(self.save_both)

        self.load_state()
        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------ UI

    def build_writing_tool(self):
        self.scratch = ScratchpadPanel(
            "Scratchpad",
            "Temporary notes. Deleted text is preserved and recoverable with Tab.",
        )
        self.final = MarkdownPanel()
        self.writing_splitter = QSplitter(Qt.Orientation.Vertical)
        self.writing_splitter.addWidget(self.scratch)
        self.writing_splitter.addWidget(self.final)
        self.writing_splitter.setSizes([390, 510])
        self.writing_page = QWidget()
        writing_layout = QVBoxLayout(self.writing_page)
        writing_layout.setContentsMargins(0, 0, 0, 0)
        writing_layout.addWidget(self.writing_splitter)

    def create_workspace_dock(self, title, object_name, widget):
        dock = QDockWidget(title, self)
        dock.setObjectName(object_name)
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        dock.setWidget(widget)
        return dock

    def register_tool_dock(self, key, dock, area):
        tool = dock.widget()
        if tool is None:
            raise RuntimeError(f"Tool dock {key!r} has no content widget")
        # Replace the dock's managed content before handing the tool to the
        # host.  QDockWidget's internal layout must never retain the tool while
        # that tool is attached to a center-pane layout.
        host = ToolHost(None, dock)
        dock.setWidget(host)
        host.set_tool(tool)
        self.tool_docks[key] = dock
        self.tool_hosts[key] = host
        self.tool_widgets[key] = tool
        self.tool_last_areas[key] = area
        self.addDockWidget(area, dock)
        dock.dockLocationChanged.connect(
            lambda new_area, tool_key=key: self.remember_tool_area(tool_key, new_area)
        )

    def build_tool_docks(self):
        writing_dock = self.create_workspace_dock(
            "Writing", "writingDock", self.writing_page
        )
        self.register_tool_dock(
            "writing", writing_dock, self.TOOL_DEFAULT_AREAS["writing"]
        )

        self.calculator = CalculatorDock(self)
        self.register_tool_dock(
            "calculator", self.calculator, self.TOOL_DEFAULT_AREAS["calculator"]
        )
        self.calculator.result_ready.connect(self.copy_calculator_result)

        self.library = self.create_workspace_dock(
            "Materials & Samples", "materialsSamplesDock", LibraryPage(self.database)
        )
        self.register_tool_dock(
            "library", self.library, self.TOOL_DEFAULT_AREAS["library"]
        )

        self.stoichiometry = self.create_workspace_dock(
            "Stoichiometry",
            "stoichiometryDock",
            StoichiometryPage(self.database, self),
        )
        self.register_tool_dock(
            "stoichiometry",
            self.stoichiometry,
            self.TOOL_DEFAULT_AREAS["stoichiometry"],
        )
        self.splitDockWidget(self.library, self.stoichiometry, Qt.Orientation.Vertical)
        self.resizeDocks(
            [self.calculator, self.library, self.stoichiometry],
            [300, 390, 390],
            Qt.Orientation.Horizontal,
        )

    def build_workspace_explorer(self):
        self.workspace_explorer = WorkspaceExplorer(self)
        self.workspace_explorer.workspace_requested.connect(self.switch_workspace)
        self.workspace_explorer.document_requested.connect(self.open_workspace_document)
        self.workspace_explorer.new_requested.connect(self.new_workspace)
        self.workspace_explorer.rename_requested.connect(self.rename_workspace)
        self.explorer_dock = self.create_workspace_dock(
            "Workspace Explorer", "workspaceExplorerDock", self.workspace_explorer
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.explorer_dock)
        self.resizeDocks(
            [self.explorer_dock], [260], Qt.Orientation.Horizontal
        )

    def build_actions(self):
        self.new_action = QAction(
            "New Final Document",
            self,
            shortcut=QKeySequence.StandardKey.New,
            triggered=self.new_final,
        )
        self.open_action = QAction(
            "Open...", self, shortcut=QKeySequence.StandardKey.Open, triggered=self.open_final
        )
        self.save_action = QAction(
            "Save", self, shortcut=QKeySequence.StandardKey.Save, triggered=self.save_final_file
        )
        self.save_as_action = QAction(
            "Save As...",
            self,
            shortcut=QKeySequence.StandardKey.SaveAs,
            triggered=self.save_final_as,
        )
        self.export_final_action = QAction(
            "Export Final Markdown...", self, triggered=self.save_final_as
        )
        self.export_all_action = QAction(
            "Export Complete Workspace...", self, triggered=self.export_workspace
        )
        self.find_action = QAction(
            "Find...", self, shortcut=QKeySequence.StandardKey.Find, triggered=self.find_text
        )
        self.insert_image_action = QAction("Insert Image...", self, triggered=self.insert_image)
        self.insert_link_action = QAction("Insert Link...", self, triggered=self.insert_link)
        self.insert_table_action = QAction(
            "Insert Table",
            self,
            triggered=lambda: self.final.insert_markdown(
                "| Column 1 | Column 2 |\n| --- | --- |\n|  |  |\n"
            ),
        )
        self.insert_task_action = QAction(
            "Insert Task List",
            self,
            triggered=lambda: self.final.insert_markdown("- [ ] Task\n"),
        )
        self.insert_code_action = QAction(
            "Insert Code Block",
            self,
            triggered=lambda: self.final.insert_markdown("```text\n\n```\n"),
        )
        self.new_workspace_action = QAction(
            "New Workspace...", self, triggered=self.new_workspace
        )
        self.explorer_action = QAction(
            "Workspace Explorer", self, triggered=self.toggle_explorer
        )
        self.theme_action = QAction("Toggle Light/Dark", self, triggered=self.toggle_theme)
        self.about_action = QAction("About", self, triggered=self.about)

        self.tool_actions = {}
        self.main_tool_actions = {}
        for key, title in self.TOOL_TITLES.items():
            self.tool_actions[key] = QAction(
                title, self, triggered=lambda checked=False, tool_key=key: self.toggle_tool(tool_key)
            )
            self.main_tool_actions[key] = QAction(
                title,
                self,
                triggered=lambda checked=False, tool_key=key: self.move_tool_to_center(tool_key, 0),
            )

    def build_menus(self):
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(self.new_workspace_action)
        file_menu.addSeparator()
        for action in (
            self.new_action,
            self.open_action,
            self.save_action,
            self.save_as_action,
            self.export_final_action,
            self.export_all_action,
        ):
            file_menu.addAction(action)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        edit_menu = self.menuBar().addMenu("Edit")
        edit_menu.addAction(self.find_action)
        insert_menu = edit_menu.addMenu("Insert")
        for action in (
            self.insert_image_action,
            self.insert_link_action,
            self.insert_table_action,
            self.insert_task_action,
            self.insert_code_action,
        ):
            insert_menu.addAction(action)

        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(self.explorer_action)
        tools_menu = view_menu.addMenu("Open Tool")
        main_menu = view_menu.addMenu("Make Main")
        for key in self.TOOL_TITLES:
            tools_menu.addAction(self.tool_actions[key])
            main_menu.addAction(self.main_tool_actions[key])
        view_menu.addSeparator()
        view_menu.addAction(self.theme_action)
        self.menuBar().addMenu("Help").addAction(self.about_action)

    def build_toolbar(self):
        bar = self.addToolBar("Main")
        bar.setObjectName("MainToolBar")
        bar.setMovable(False)
        for action in (
            self.open_action,
            self.save_action,
            self.export_all_action,
            self.find_action,
        ):
            bar.addAction(action)

    def themed_icon(self, name, fallback):
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            return icon
        return self.style().standardIcon(fallback)

    def build_activity_rail(self):
        rail = QToolBar("Activity")
        rail.setObjectName("ActivityRail")
        rail.setMovable(False)
        rail.setFloatable(False)
        rail.setOrientation(Qt.Orientation.Vertical)
        rail.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        rail.setIconSize(QSize(22, 22))
        rail.setFixedWidth(44)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, rail)
        self.activity_rail = rail

        explorer = QAction(
            self.themed_icon("folder", QStyle.StandardPixmap.SP_DirIcon),
            "Workspaces",
            self,
            triggered=self.toggle_explorer,
        )
        explorer.setToolTip("Workspaces")
        rail.addAction(explorer)
        rail.addSeparator()

        icon_specs = {
            "writing": ("accessories-text-editor", QStyle.StandardPixmap.SP_FileIcon),
            "calculator": ("accessories-calculator", QStyle.StandardPixmap.SP_ComputerIcon),
            "library": ("folder-documents", QStyle.StandardPixmap.SP_DirOpenIcon),
            "stoichiometry": ("applications-science", QStyle.StandardPixmap.SP_BrowserReload),
        }
        self.activity_actions = {"explorer": explorer}
        for key, (theme_name, fallback) in icon_specs.items():
            action = QAction(
                self.themed_icon(theme_name, fallback),
                self.TOOL_TITLES[key],
                self,
                triggered=lambda checked=False, tool_key=key: self.toggle_tool(tool_key),
            )
            action.setToolTip(self.TOOL_TITLES[key])
            rail.addAction(action)
            self.activity_actions[key] = action

    # ------------------------------------------------------------- Tool shell

    def remember_tool_area(self, key, area):
        if area != Qt.DockWidgetArea.NoDockWidgetArea:
            self.tool_last_areas[key] = area
            self.settings.setValue(f"tools/{key}/lastArea", int(area.value))

    def center_slot_for_tool(self, key):
        for index, pane in enumerate(self.center_host.panes):
            if pane.current_key == key:
                return index
        return None

    def move_tool_to_center(self, key, slot=0):
        if key not in self.tool_docks:
            return
        slot = 0 if slot not in (0, 1) else slot
        if slot == 1 and not self.center_host.split_button.isChecked():
            self.center_host.set_split_enabled(True)

        current_slot = self.center_slot_for_tool(key)
        if current_slot == slot:
            self.tool_widgets[key].show()
            self.tool_widgets[key].setFocus(Qt.FocusReason.OtherFocusReason)
            return
        if current_slot is not None:
            content = self.center_host.pane(current_slot).detach()
        else:
            dock = self.tool_docks[key]
            dock.hide()
            area = self.dockWidgetArea(dock)
            if area != Qt.DockWidgetArea.NoDockWidgetArea:
                self.remember_tool_area(key, area)
            self.removeDockWidget(dock)
            content = self.tool_hosts[key].take_tool()

        target = self.center_host.pane(slot)
        if target.current_key is not None and target.current_key != key:
            self.move_center_tool_to_dock(slot, show=False)

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
        self.tool_hosts[key].set_tool(content)
        dock = self.tool_docks[key]
        area = self.tool_last_areas.get(key, self.TOOL_DEFAULT_AREAS[key])
        self.addDockWidget(area, dock)
        if show:
            dock.show()
            dock.raise_()
        else:
            dock.hide()
        self.settings.remove(f"center/tool{slot}")

    def center_tool_requested(self, slot, key):
        if key is None:
            self.center_close_requested(slot)
        else:
            self.move_tool_to_center(str(key), slot)

    def center_dock_requested(self, slot):
        self.move_center_tool_to_dock(slot, show=True)

    def center_close_requested(self, slot):
        self.move_center_tool_to_dock(slot, show=False)
        if slot == 1:
            self.center_host.set_split_enabled(False)
            self.settings.setValue("center/split", False)

    def center_split_toggled(self, enabled):
        if not enabled and self.center_host.pane(1).current_key is not None:
            self.move_center_tool_to_dock(1, show=False)
        self.settings.setValue("center/split", bool(enabled))

    def center_orientation_changed(self, value):
        self.settings.setValue("center/orientation", int(value))

    def toggle_tool(self, key):
        slot = self.center_slot_for_tool(key)
        if slot is not None:
            self.tool_widgets[key].show()
            self.tool_widgets[key].setFocus(Qt.FocusReason.OtherFocusReason)
            return
        dock = self.tool_docks[key]
        if dock.isVisible():
            dock.hide()
        else:
            if self.dockWidgetArea(dock) == Qt.DockWidgetArea.NoDockWidgetArea:
                self.addDockWidget(
                    self.tool_last_areas.get(key, self.TOOL_DEFAULT_AREAS[key]), dock
                )
            dock.show()
            dock.raise_()

    def toggle_explorer(self):
        self.explorer_dock.setVisible(not self.explorer_dock.isVisible())
        if self.explorer_dock.isVisible():
            self.explorer_dock.raise_()

    # --------------------------------------------------------------- Workspaces

    def workspace_key(self, document_type):
        if self.current_workspace_id is None:
            raise RuntimeError("No active workspace")
        return self.database.workspace_document_key(
            self.current_workspace_id, document_type
        )

    def refresh_workspace_explorer(self):
        self.workspace_explorer.set_workspaces(
            self.database.list_workspaces(), self.current_workspace_id
        )

    def load_initial_workspace(self):
        rows = self.database.list_workspaces()
        if not rows:
            workspace_id = self.database.create_workspace("Default Workspace")
        else:
            saved = self.settings.value("activeWorkspaceId")
            valid_ids = {int(row["id"]) for row in rows}
            try:
                saved_id = int(saved) if saved is not None else None
            except (TypeError, ValueError):
                saved_id = None
            workspace_id = saved_id if saved_id in valid_ids else int(rows[0]["id"])
        self.switch_workspace(workspace_id, save_current=False)

    def switch_workspace(self, workspace_id, save_current=True):
        workspace_id = int(workspace_id)
        if self.current_workspace_id == workspace_id:
            self.refresh_workspace_explorer()
            return
        row = self.database.workspace(workspace_id)
        if row is None or row["archived_at"] is not None:
            return
        if save_current and self.current_workspace_id is not None:
            self.save_both()

        self.loading = True
        self.current_workspace_id = workspace_id
        self.database.ensure_workspace_documents(workspace_id)
        self.scratch.set_initial_text(
            self.database.get_workspace_text(workspace_id, "scratchpad")
        )
        self.final.set_text(self.database.get_workspace_text(workspace_id, "final"))
        latest = self.database.latest_deleted_fragment(self.workspace_key("scratchpad"))
        if latest:
            self.scratch.set_ghost(latest["fragment"])
        else:
            self.scratch.clear_ghost()
        self.load_workspace_file()
        self.loading = False

        self.settings.setValue("activeWorkspaceId", workspace_id)
        self.refresh_workspace_explorer()
        self.update_window_title()
        self.statusBar().showMessage(f"Opened workspace: {row['name']}", 2000)

    def new_workspace(self):
        name, ok = QInputDialog.getText(self, "New Workspace", "Workspace name:")
        if not ok:
            return
        workspace_id = self.database.create_workspace(name)
        self.switch_workspace(workspace_id)
        self.explorer_dock.show()
        self.explorer_dock.raise_()

    def rename_workspace(self, workspace_id):
        row = self.database.workspace(workspace_id)
        if row is None:
            return
        name, ok = QInputDialog.getText(
            self, "Rename Workspace", "Workspace name:", text=row["name"]
        )
        if not ok:
            return
        try:
            self.database.rename_workspace(workspace_id, name)
        except ValueError as error:
            QMessageBox.warning(self, "Rename Workspace", str(error))
            return
        self.refresh_workspace_explorer()
        self.update_window_title()

    def open_workspace_document(self, workspace_id, document_type):
        self.switch_workspace(workspace_id)
        self.move_tool_to_center("writing", 0)
        if document_type == "scratchpad":
            self.scratch.editor.setFocus()
        else:
            self.final.editor.setFocus()

    # ------------------------------------------------------------ Writing state

    def connect_editors(self):
        self.scratch.editor.textChanged.connect(self.schedule_autosave)
        self.final.editor.textChanged.connect(self.schedule_autosave)
        self.scratch.history_requested.connect(
            lambda: self.show_history(
                self.workspace_key("scratchpad"), self.scratch.editor.toPlainText()
            )
        )
        self.final.history_requested.connect(
            lambda: self.show_history(self.workspace_key("final"), self.final.text())
        )
        self.scratch.checkpoint_requested.connect(
            lambda: self.checkpoint(
                self.workspace_key("scratchpad"), self.scratch.editor.toPlainText()
            )
        )
        self.final.checkpoint_requested.connect(
            lambda: self.checkpoint(self.workspace_key("final"), self.final.text())
        )
        self.scratch.deletion_detected.connect(self.record_deletion)
        self.scratch.recover_requested.connect(self.recover_deleted)

    def load_state(self):
        try:
            layout_version = int(self.settings.value("layoutStateVersion", 0))
        except (TypeError, ValueError):
            layout_version = 0
        layout_is_current = layout_version == self.LAYOUT_STATE_VERSION
        geometry = self.settings.value("geometryV2") if layout_is_current else None
        state = self.settings.value("windowStateV2") if layout_is_current else None
        writing_splitter = self.settings.value("writingSplitter")
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)
        if writing_splitter:
            self.writing_splitter.restoreState(writing_splitter)

        for key, default_area in self.TOOL_DEFAULT_AREAS.items():
            value = self.settings.value(f"tools/{key}/lastArea")
            if value is not None:
                try:
                    self.tool_last_areas[key] = Qt.DockWidgetArea(int(value))
                except (TypeError, ValueError):
                    self.tool_last_areas[key] = default_area
            else:
                area = self.dockWidgetArea(self.tool_docks[key])
                if area != Qt.DockWidgetArea.NoDockWidgetArea:
                    self.tool_last_areas[key] = area

        self.load_initial_workspace()

        orientation = self.settings.value(
            "center/orientation", int(Qt.Orientation.Horizontal.value)
        )
        try:
            self.center_host.set_orientation(Qt.Orientation(int(orientation)))
        except (TypeError, ValueError):
            self.center_host.set_orientation(Qt.Orientation.Horizontal)

        primary = self.settings.value("center/tool0", "writing")
        secondary = self.settings.value("center/tool1", "")
        split = str(self.settings.value("center/split", "false")).lower() in (
            "1",
            "true",
            "yes",
        )
        if primary not in self.tool_docks:
            primary = "writing"
        self.move_tool_to_center(primary, 0)
        if split and secondary in self.tool_docks and secondary != primary:
            self.center_host.set_split_enabled(True)
            self.move_tool_to_center(secondary, 1)
        else:
            self.center_host.set_split_enabled(False)

    def workspace_file_setting_key(self):
        return f"workspace/{self.current_workspace_id}/currentFile"

    def load_workspace_file(self):
        value = self.settings.value(self.workspace_file_setting_key(), "")
        path = Path(value) if value else None
        if path and path.is_file():
            self.current_file = path
        else:
            self.current_file = None
        self.final.set_document_path(self.current_file)
        self.final.update_preview()

    def set_current_file(self, path):
        self.current_file = Path(path) if path else None
        self.final.set_document_path(self.current_file)
        if self.current_workspace_id is not None:
            key = self.workspace_file_setting_key()
            if self.current_file:
                self.settings.setValue(key, str(self.current_file))
            else:
                self.settings.remove(key)
        self.update_window_title()

    def update_window_title(self):
        workspace = (
            self.database.workspace(self.current_workspace_id)
            if self.current_workspace_id is not None
            else None
        )
        name = workspace["name"] if workspace else "No Workspace"
        if self.current_file:
            self.setWindowTitle(f"Lab Workspace — {name} — {self.current_file.name}")
        else:
            self.setWindowTitle(f"Lab Workspace — {name}")

    def schedule_autosave(self):
        if not self.loading:
            self.autosave.start()

    def save_both(self):
        if self.current_workspace_id is None:
            return False
        changed = self.database.save_workspace_text(
            self.current_workspace_id,
            "scratchpad",
            self.scratch.editor.toPlainText(),
        )
        changed |= self.database.save_workspace_text(
            self.current_workspace_id, "final", self.final.text()
        )
        if changed:
            self.refresh_workspace_explorer()
            self.statusBar().showMessage(
                "Autosaved workspace locally with immutable history", 2500
            )
        return changed

    def record_deletion(self, fragment, position):
        key = self.workspace_key("scratchpad")
        self.database.record_deleted_fragment(key, fragment, position)
        self.database.save_workspace_text(
            self.current_workspace_id,
            "scratchpad",
            self.scratch.editor.toPlainText(),
            "text deleted",
            True,
        )
        self.scratch.set_ghost(fragment)

    def recover_deleted(self):
        key = self.workspace_key("scratchpad")
        row = self.database.latest_deleted_fragment(key)
        if not row:
            self.statusBar().showMessage("No unrecovered deleted text", 2000)
            return
        self.scratch.insert_recovered(row["fragment"], row["position"])
        self.database.mark_fragment_recovered(row["id"])
        self.database.save_workspace_text(
            self.current_workspace_id,
            "scratchpad",
            self.scratch.editor.toPlainText(),
            f"recovered deletion {row['id']}",
            True,
        )
        next_row = self.database.latest_deleted_fragment(key)
        self.scratch.set_ghost(next_row["fragment"]) if next_row else self.scratch.clear_ghost()
        self.statusBar().showMessage("Deleted text recovered", 2500)

    def checkpoint(self, key, text):
        reason, ok = QInputDialog.getText(
            self, "Create Checkpoint", "Checkpoint label:"
        )
        if ok:
            self.database.save_text(key, text, reason.strip() or "manual checkpoint", True)
            self.database.touch_workspace(self.current_workspace_id)

    def show_history(self, key, current_text):
        self.save_both()
        dialog = HistoryDialog(self.database, key, current_text, self)
        dialog.restore_requested.connect(
            lambda revision_id: self.restore_revision(key, revision_id)
        )
        dialog.exec()

    def restore_revision(self, key, revision_id):
        row = self.database.revision(revision_id)
        if not row:
            return
        if key == self.workspace_key("scratchpad"):
            self.scratch.set_initial_text(row["text"])
        else:
            self.final.set_text(row["text"])
        self.database.save_text(key, row["text"], f"restored revision {revision_id}", True)
        self.database.touch_workspace(self.current_workspace_id)

    # -------------------------------------------------------------- File/editor

    def new_final(self):
        if (
            QMessageBox.question(
                self,
                "New Document",
                "Clear the final document? Its history remains permanent in this workspace.",
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.final.set_text("")
            self.set_current_file(None)
            self.database.save_workspace_text(
                self.current_workspace_id, "final", "", "new document", True
            )

    def open_final(self):
        name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown or Text",
            "",
            "Markdown/Text (*.md *.txt);;All files (*)",
        )
        if not name:
            return
        try:
            text = Path(name).read_text(encoding="utf-8")
        except Exception as error:
            QMessageBox.critical(self, "Open Failed", str(error))
            return
        self.set_current_file(name)
        self.final.set_text(text)
        self.database.save_workspace_text(
            self.current_workspace_id,
            "final",
            text,
            f"opened {self.current_file.name}",
            True,
        )
        self.move_tool_to_center("writing", 0)

    def save_final_file(self):
        if self.current_file is None:
            return self.save_final_as()
        try:
            self.current_file.write_text(self.final.text(), encoding="utf-8")
        except Exception as error:
            QMessageBox.critical(self, "Save Failed", str(error))
            return False
        self.database.save_workspace_text(
            self.current_workspace_id,
            "final",
            self.final.text(),
            f"saved {self.current_file.name}",
            True,
        )
        self.set_current_file(self.current_file)
        return True

    def save_final_as(self):
        name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Final Markdown",
            str(EXPORT_DIR / "lab_note.md"),
            "Markdown (*.md);;Text (*.txt)",
        )
        if not name:
            return False
        self.set_current_file(name)
        return self.save_final_file()

    def export_workspace(self):
        workspace = self.database.workspace(self.current_workspace_id)
        default_name = (
            workspace["name"].strip().replace(" ", "_") if workspace else "workspace"
        )
        name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Complete Workspace",
            str(EXPORT_DIR / f"{default_name}_export.md"),
            "Markdown (*.md)",
        )
        if not name:
            return
        workspace_title = workspace["name"] if workspace else "Lab Workspace"
        content = (
            f"# {workspace_title}\n\n"
            f"## Scratchpad\n\n{self.scratch.editor.toPlainText()}\n\n"
            f"## Final Document\n\n{self.final.text()}\n"
        )
        try:
            Path(name).write_text(content, encoding="utf-8")
        except Exception as error:
            QMessageBox.critical(self, "Export Failed", str(error))

    def find_text(self):
        editor = self.focusWidget()
        candidates = (self.scratch.editor, self.final.editor, self.final.split_editor)
        if editor not in candidates:
            editor = self.final.editor
        term, ok = QInputDialog.getText(self, "Find", "Text to find:")
        if ok and term and not editor.find(term):
            QMessageBox.information(
                self, "Find", "Text not found from the current cursor position."
            )

    def insert_image(self):
        name, _ = QFileDialog.getOpenFileName(
            self,
            "Insert Image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp *.svg);;All files (*)",
        )
        if name:
            self.final.insert_image(Path(name))

    def insert_link(self):
        label, ok = QInputDialog.getText(self, "Insert Link", "Link text:")
        if not ok:
            return
        url, ok = QInputDialog.getText(self, "Insert Link", "URL:")
        if ok and url.strip():
            self.final.insert_markdown(
                f"[{label.strip() or url.strip()}]({url.strip()})"
            )

    def append_markdown(self, text):
        self.final.editor.appendPlainText("\n" + text)
        self.final.update_preview()

    def copy_calculator_result(self, result):
        QApplication.clipboard().setText(result)
        self.statusBar().showMessage("Calculator result copied", 2000)

    def toggle_theme(self):
        name = "dark" if self.settings.value("theme", "light") == "light" else "light"
        self.settings.setValue("theme", name)
        apply_theme(QApplication.instance(), name)

    def about(self):
        QMessageBox.about(
            self,
            "About",
            "Lab Workspace\nNamed workspaces with a rearrangeable tool shell, Markdown writing, materials and samples, stoichiometry, and scientific calculations.\n\nVerify scientific calculations independently.",
        )

    def closeEvent(self, event):
        self.autosave.stop()
        self.save_both()
        self.settings.setValue("layoutStateVersion", self.LAYOUT_STATE_VERSION)
        self.settings.setValue("geometryV2", self.saveGeometry())
        self.settings.setValue("windowStateV2", self.saveState())
        self.settings.setValue("writingSplitter", self.writing_splitter.saveState())
        self.settings.setValue(
            "center/orientation", int(self.center_host.splitter.orientation().value)
        )
        self.settings.setValue("center/split", self.center_host.split_button.isChecked())
        for index, pane in enumerate(self.center_host.panes):
            if pane.current_key:
                self.settings.setValue(f"center/tool{index}", pane.current_key)
            else:
                self.settings.remove(f"center/tool{index}")
        event.accept()
