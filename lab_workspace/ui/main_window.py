from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QDockWidget, QFileDialog, QInputDialog, QMainWindow, QMessageBox, QSplitter, QVBoxLayout, QWidget

from lab_workspace.core.config import EXPORT_DIR
from lab_workspace.ui.calculator_dock import CalculatorDock
from lab_workspace.ui.history_dialog import HistoryDialog
from lab_workspace.ui.library import LibraryPage
from lab_workspace.ui.markdown_panel import MarkdownPanel
from lab_workspace.ui.scratchpad_panel import ScratchpadPanel
from lab_workspace.ui.stoichiometry import StoichiometryPage
from lab_workspace.ui.theme import apply_theme


class MainWindow(QMainWindow):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.settings = QSettings()
        self.current_file = None
        self.loading = False
        self.setWindowTitle("Lab Workspace")
        self.resize(1500, 900)
        self.setDockOptions(
            QMainWindow.DockOption.AnimatedDocks
            | QMainWindow.DockOption.AllowNestedDocks
            | QMainWindow.DockOption.AllowTabbedDocks
            | QMainWindow.DockOption.GroupedDragging
        )
        apply_theme(QApplication.instance(), self.settings.value("theme", "light"))

        self.scratch = ScratchpadPanel("Scratchpad", "Temporary notes. Deleted text is preserved and recoverable with Tab.")
        self.final = MarkdownPanel()
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.scratch)
        self.splitter.addWidget(self.final)
        self.splitter.setSizes([390, 510])
        writing_page = QWidget()
        writing_layout = QVBoxLayout(writing_page)
        writing_layout.setContentsMargins(0, 0, 0, 0)
        writing_layout.addWidget(self.splitter)

        self.setCentralWidget(writing_page)

        self.calculator = CalculatorDock(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.calculator)
        self.library = self.create_workspace_dock("Materials & Samples", "materialsSamplesDock", LibraryPage(database))
        self.stoichiometry = self.create_workspace_dock("Stoichiometry", "stoichiometryDock", StoichiometryPage(database, self))
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.library)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.stoichiometry)
        self.splitDockWidget(self.library, self.stoichiometry, Qt.Orientation.Vertical)
        self.resizeDocks([self.calculator, self.library, self.stoichiometry], [300, 390, 390], Qt.Orientation.Horizontal)
        self.calculator.result_ready.connect(self.copy_calculator_result)
        self.build_actions()
        self.build_menus()
        self.build_toolbar()
        self.connect_editors()
        self.load_state()
        self.autosave = QTimer(self)
        self.autosave.setSingleShot(True)
        self.autosave.setInterval(1200)
        self.autosave.timeout.connect(self.save_both)
        self.statusBar().showMessage("Ready")

    def create_workspace_dock(self, title, object_name, widget):
        dock = QDockWidget(title, self)
        dock.setObjectName(object_name)
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        dock.setWidget(widget)
        return dock

    def build_actions(self):
        self.new_action = QAction("New Final Document", self, shortcut=QKeySequence.StandardKey.New, triggered=self.new_final)
        self.open_action = QAction("Open...", self, shortcut=QKeySequence.StandardKey.Open, triggered=self.open_final)
        self.save_action = QAction("Save", self, shortcut=QKeySequence.StandardKey.Save, triggered=self.save_final_file)
        self.save_as_action = QAction("Save As...", self, shortcut=QKeySequence.StandardKey.SaveAs, triggered=self.save_final_as)
        self.export_final_action = QAction("Export Final Markdown...", self, triggered=self.save_final_as)
        self.export_all_action = QAction("Export Complete Workspace...", self, triggered=self.export_workspace)
        self.find_action = QAction("Find...", self, shortcut=QKeySequence.StandardKey.Find, triggered=self.find_text)
        self.insert_image_action = QAction("Insert Image...", self, triggered=self.insert_image)
        self.insert_link_action = QAction("Insert Link...", self, triggered=self.insert_link)
        self.insert_table_action = QAction("Insert Table", self, triggered=lambda: self.final.insert_markdown("| Column 1 | Column 2 |\n| --- | --- |\n|  |  |\n"))
        self.insert_task_action = QAction("Insert Task List", self, triggered=lambda: self.final.insert_markdown("- [ ] Task\n"))
        self.insert_code_action = QAction("Insert Code Block", self, triggered=lambda: self.final.insert_markdown("```text\n\n```\n"))
        self.calc_action = self.calculator.toggleViewAction()
        self.calc_action.setText("Science Calculator")
        self.library_action = self.library.toggleViewAction()
        self.library_action.setText("Materials & Samples")
        self.stoichiometry_action = self.stoichiometry.toggleViewAction()
        self.stoichiometry_action.setText("Stoichiometry")
        self.theme_action = QAction("Toggle Light/Dark", self, triggered=self.toggle_theme)
        self.about_action = QAction("About", self, triggered=self.about)

    def build_menus(self):
        file_menu = self.menuBar().addMenu("File")
        for action in (self.new_action, self.open_action, self.save_action, self.save_as_action, self.export_final_action, self.export_all_action):
            file_menu.addAction(action)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        edit_menu = self.menuBar().addMenu("Edit")
        edit_menu.addAction(self.find_action)
        insert_menu = edit_menu.addMenu("Insert")
        for action in (self.insert_image_action, self.insert_link_action, self.insert_table_action, self.insert_task_action, self.insert_code_action):
            insert_menu.addAction(action)
        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(self.calc_action)
        view_menu.addAction(self.library_action)
        view_menu.addAction(self.stoichiometry_action)
        view_menu.addAction(self.theme_action)
        self.menuBar().addMenu("Help").addAction(self.about_action)

    def build_toolbar(self):
        bar = self.addToolBar("Main")
        bar.setMovable(False)
        for action in (self.open_action, self.save_action, self.export_all_action, self.find_action, self.calc_action):
            bar.addAction(action)

    def connect_editors(self):
        self.scratch.editor.textChanged.connect(self.schedule_autosave)
        self.final.editor.textChanged.connect(self.schedule_autosave)
        self.scratch.history_requested.connect(lambda: self.show_history("scratchpad", self.scratch.editor.toPlainText()))
        self.final.history_requested.connect(lambda: self.show_history("final", self.final.text()))
        self.scratch.checkpoint_requested.connect(lambda: self.checkpoint("scratchpad", self.scratch.editor.toPlainText()))
        self.final.checkpoint_requested.connect(lambda: self.checkpoint("final", self.final.text()))
        self.scratch.deletion_detected.connect(self.record_deletion)
        self.scratch.recover_requested.connect(self.recover_deleted)

    def load_state(self):
        self.loading = True
        self.scratch.set_initial_text(self.database.get_text("scratchpad"))
        self.final.set_text(self.database.get_text("final"))
        self.loading = False
        saved_file = self.settings.value("currentFile", "")
        if saved_file and Path(saved_file).is_file():
            self.set_current_file(saved_file)
            self.final.update_preview()
        latest = self.database.latest_deleted_fragment()
        if latest:
            self.scratch.set_ghost(latest["fragment"])
        geometry = self.settings.value("geometry")
        state = self.settings.value("windowState")
        splitter = self.settings.value("splitter")
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)
        if splitter:
            self.splitter.restoreState(splitter)

    def set_current_file(self, path):
        self.current_file = Path(path) if path else None
        self.final.set_document_path(self.current_file)
        if self.current_file:
            self.settings.setValue("currentFile", str(self.current_file))
            self.setWindowTitle(f"Lab Workspace - {self.current_file.name}")
        else:
            self.settings.remove("currentFile")
            self.setWindowTitle("Lab Workspace")

    def schedule_autosave(self):
        if not self.loading:
            self.autosave.start()

    def save_both(self):
        changed = self.database.save_text("scratchpad", self.scratch.editor.toPlainText())
        changed |= self.database.save_text("final", self.final.text())
        if changed:
            self.statusBar().showMessage("Autosaved locally with immutable history", 2500)

    def record_deletion(self, fragment, position):
        self.database.record_deleted_fragment("scratchpad", fragment, position)
        self.database.save_text("scratchpad", self.scratch.editor.toPlainText(), "text deleted", True)
        self.scratch.set_ghost(fragment)

    def recover_deleted(self):
        row = self.database.latest_deleted_fragment()
        if not row:
            self.statusBar().showMessage("No unrecovered deleted text", 2000)
            return
        self.scratch.insert_recovered(row["fragment"], row["position"])
        self.database.mark_fragment_recovered(row["id"])
        self.database.save_text("scratchpad", self.scratch.editor.toPlainText(), f"recovered deletion {row['id']}", True)
        next_row = self.database.latest_deleted_fragment()
        self.scratch.set_ghost(next_row["fragment"]) if next_row else self.scratch.clear_ghost()
        self.statusBar().showMessage("Deleted text recovered", 2500)

    def checkpoint(self, key, text):
        reason, ok = QInputDialog.getText(self, "Create Checkpoint", "Checkpoint label:")
        if ok:
            self.database.save_text(key, text, reason.strip() or "manual checkpoint", True)

    def show_history(self, key, current_text):
        self.save_both()
        dialog = HistoryDialog(self.database, key, current_text, self)
        dialog.restore_requested.connect(lambda revision_id: self.restore_revision(key, revision_id))
        dialog.exec()

    def restore_revision(self, key, revision_id):
        row = self.database.revision(revision_id)
        if not row:
            return
        if key == "scratchpad":
            self.scratch.set_initial_text(row["text"])
        else:
            self.final.set_text(row["text"])
        self.database.save_text(key, row["text"], f"restored revision {revision_id}", True)

    def new_final(self):
        if QMessageBox.question(self, "New Document", "Clear the final document? Its history remains permanent.") == QMessageBox.StandardButton.Yes:
            self.final.set_text("")
            self.set_current_file(None)
            self.database.save_text("final", "", "new document", True)

    def open_final(self):
        name, _ = QFileDialog.getOpenFileName(self, "Open Markdown or Text", "", "Markdown/Text (*.md *.txt);;All files (*)")
        if not name:
            return
        try:
            text = Path(name).read_text(encoding="utf-8")
        except Exception as error:
            QMessageBox.critical(self, "Open Failed", str(error))
            return
        self.set_current_file(name)
        self.final.set_text(text)
        self.database.save_text("final", text, f"opened {self.current_file.name}", True)

    def save_final_file(self):
        if self.current_file is None:
            return self.save_final_as()
        try:
            self.current_file.write_text(self.final.text(), encoding="utf-8")
        except Exception as error:
            QMessageBox.critical(self, "Save Failed", str(error))
            return False
        self.database.save_text("final", self.final.text(), f"saved {self.current_file.name}", True)
        self.set_current_file(self.current_file)
        return True

    def save_final_as(self):
        name, _ = QFileDialog.getSaveFileName(self, "Save Final Markdown", str(EXPORT_DIR / "lab_note.md"), "Markdown (*.md);;Text (*.txt)")
        if not name:
            return False
        self.set_current_file(name)
        return self.save_final_file()

    def export_workspace(self):
        name, _ = QFileDialog.getSaveFileName(self, "Export Complete Workspace", str(EXPORT_DIR / "lab_workspace_export.md"), "Markdown (*.md)")
        if not name:
            return
        content = f"# Lab Workspace Export\n\n## Scratchpad\n\n{self.scratch.editor.toPlainText()}\n\n## Final Document\n\n{self.final.text()}\n"
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
            QMessageBox.information(self, "Find", "Text not found from the current cursor position.")

    def insert_image(self):
        name, _ = QFileDialog.getOpenFileName(self, "Insert Image", "", "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp *.svg);;All files (*)")
        if name:
            self.final.insert_image(Path(name))

    def insert_link(self):
        label, ok = QInputDialog.getText(self, "Insert Link", "Link text:")
        if not ok:
            return
        url, ok = QInputDialog.getText(self, "Insert Link", "URL:")
        if ok and url.strip():
            self.final.insert_markdown(f"[{label.strip() or url.strip()}]({url.strip()})")

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
        QMessageBox.about(self, "About", "Lab Workspace\nMarkdown writing, materials and samples, stoichiometry, and scientific calculations.\n\nVerify scientific calculations independently.")

    def closeEvent(self, event):
        self.autosave.stop()
        self.save_both()
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("splitter", self.splitter.saveState())
        event.accept()
