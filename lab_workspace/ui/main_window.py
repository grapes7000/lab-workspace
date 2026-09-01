from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QAction, QKeySequence, QTextDocument
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QFileDialog, QMessageBox, QInputDialog, QApplication
)
from lab_workspace.ui.editor_panel import EditorPanel
from lab_workspace.ui.calculator_dock import CalculatorDock
from lab_workspace.ui.history_dialog import HistoryDialog
from lab_workspace.ui.theme import apply_theme
from lab_workspace.core.config import EXPORT_DIR


class MainWindow(QMainWindow):
    def __init__(self, database):
        super().__init__(); self.database = database; self.settings = QSettings()
        self.current_file = None; self.loading = False
        self.setWindowTitle("Lab Workspace v1"); self.resize(1300, 850)
        self.scratch = EditorPanel("Scratchpad", "Temporary notes. Autosaved with revision history.")
        self.final = EditorPanel("Final Document", "Write the polished laboratory note or report here.")
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.scratch); self.splitter.addWidget(self.final); self.splitter.setSizes([390, 410])
        self.setCentralWidget(self.splitter)
        self.calculator = CalculatorDock(self); self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.calculator)
        self.calculator.result_ready.connect(self.copy_calculator_result)
        self.build_actions(); self.build_menus(); self.build_toolbar(); self.connect_editors(); self.load_state()
        self.autosave = QTimer(self); self.autosave.setSingleShot(True); self.autosave.setInterval(1200); self.autosave.timeout.connect(self.save_both)
        self.statusBar().showMessage("Ready")

    def build_actions(self):
        self.new_action = QAction("New Final Document", self, shortcut=QKeySequence.StandardKey.New, triggered=self.new_final)
        self.open_action = QAction("Open...", self, shortcut=QKeySequence.StandardKey.Open, triggered=self.open_final)
        self.save_action = QAction("Save", self, shortcut=QKeySequence.StandardKey.Save, triggered=self.save_final_file)
        self.save_as_action = QAction("Save As...", self, shortcut=QKeySequence.StandardKey.SaveAs, triggered=self.save_final_as)
        self.export_action = QAction("Export Markdown...", self, triggered=self.export_markdown)
        self.find_action = QAction("Find...", self, shortcut=QKeySequence.StandardKey.Find, triggered=self.find_text)
        self.calc_action = self.calculator.toggleViewAction(); self.calc_action.setText("Science Calculator")
        self.theme_action = QAction("Toggle Light/Dark", self, triggered=self.toggle_theme)
        self.about_action = QAction("About", self, triggered=self.about)

    def build_menus(self):
        file_menu = self.menuBar().addMenu("File")
        for action in (self.new_action,self.open_action,self.save_action,self.save_as_action,self.export_action): file_menu.addAction(action)
        file_menu.addSeparator(); file_menu.addAction("Exit", self.close)
        edit = self.menuBar().addMenu("Edit"); edit.addAction(self.find_action)
        view = self.menuBar().addMenu("View"); view.addAction(self.calc_action); view.addAction(self.theme_action)
        help_menu = self.menuBar().addMenu("Help"); help_menu.addAction(self.about_action)

    def build_toolbar(self):
        toolbar = self.addToolBar("Main"); toolbar.setMovable(False)
        for action in (self.open_action,self.save_action,self.export_action,self.find_action,self.calc_action): toolbar.addAction(action)

    def connect_editors(self):
        for panel, key in ((self.scratch,"scratchpad"),(self.final,"final")):
            panel.editor.textChanged.connect(self.schedule_autosave)
            panel.history_requested.connect(lambda checked=False, k=key, p=panel: self.show_history(k,p))
            panel.checkpoint_requested.connect(lambda checked=False, k=key, p=panel: self.checkpoint(k,p))

    def load_state(self):
        self.loading = True
        self.scratch.editor.setPlainText(self.database.get_text("scratchpad"))
        self.final.editor.setPlainText(self.database.get_text("final"))
        self.loading = False
        geometry = self.settings.value("geometry"); state = self.settings.value("windowState")
        splitter = self.settings.value("splitter")
        if geometry: self.restoreGeometry(geometry)
        if state: self.restoreState(state)
        if splitter: self.splitter.restoreState(splitter)

    def schedule_autosave(self):
        if not self.loading: self.autosave.start()

    def save_both(self):
        changed = False
        changed |= self.database.save_text("scratchpad", self.scratch.editor.toPlainText())
        changed |= self.database.save_text("final", self.final.editor.toPlainText())
        if changed: self.statusBar().showMessage("Autosaved locally", 2500)

    def checkpoint(self, key, panel):
        reason, ok = QInputDialog.getText(self, "Create Checkpoint", "Checkpoint label:")
        if ok:
            self.database.save_text(key, panel.editor.toPlainText(), reason.strip() or "manual checkpoint", True)
            self.statusBar().showMessage("Checkpoint created", 2500)

    def show_history(self, key, panel):
        self.save_both(); dialog = HistoryDialog(self.database,key,panel.editor.toPlainText(),self)
        dialog.restore_requested.connect(lambda revision_id: self.restore_revision(key,panel,revision_id))
        dialog.exec()

    def restore_revision(self, key, panel, revision_id):
        revision = self.database.revision(revision_id)
        if not revision: return
        panel.editor.setPlainText(revision["text"])
        self.database.save_text(key, revision["text"], f"restored revision {revision_id}", True)

    def new_final(self):
        if QMessageBox.question(self,"New Document","Clear the final document? Current text remains in history.") == QMessageBox.StandardButton.Yes:
            self.final.editor.clear(); self.current_file = None; self.database.save_text("final","","new document",True)

    def open_final(self):
        name, _ = QFileDialog.getOpenFileName(self,"Open Text Document","","Text documents (*.md *.txt);;All files (*)")
        if not name: return
        try:
            text = Path(name).read_text(encoding="utf-8")
        except Exception as error:
            QMessageBox.critical(self,"Open Failed",str(error)); return
        self.final.editor.setPlainText(text); self.current_file = Path(name)
        self.database.save_text("final",text,f"opened {self.current_file.name}",True)
        self.setWindowTitle(f"Lab Workspace v1 - {self.current_file.name}")

    def save_final_file(self):
        if self.current_file is None: return self.save_final_as()
        try: self.current_file.write_text(self.final.editor.toPlainText(),encoding="utf-8")
        except Exception as error: QMessageBox.critical(self,"Save Failed",str(error)); return False
        self.database.save_text("final",self.final.editor.toPlainText(),f"saved {self.current_file.name}",True)
        self.statusBar().showMessage(f"Saved {self.current_file}",3000); return True

    def save_final_as(self):
        name, _ = QFileDialog.getSaveFileName(self,"Save Final Document",str(EXPORT_DIR/"lab_note.md"),"Markdown (*.md);;Text (*.txt)")
        if not name: return False
        self.current_file = Path(name); self.setWindowTitle(f"Lab Workspace v1 - {self.current_file.name}")
        return self.save_final_file()

    def export_markdown(self):
        name, _ = QFileDialog.getSaveFileName(self,"Export Markdown",str(EXPORT_DIR/"lab_workspace_export.md"),"Markdown (*.md)")
        if not name: return
        content = f"# Lab Workspace Export\n\n## Scratchpad\n\n{self.scratch.editor.toPlainText()}\n\n## Final Document\n\n{self.final.editor.toPlainText()}\n"
        try: Path(name).write_text(content,encoding="utf-8")
        except Exception as error: QMessageBox.critical(self,"Export Failed",str(error)); return
        self.statusBar().showMessage(f"Exported {name}",3000)

    def find_text(self):
        editor = self.focusWidget()
        if editor not in (self.scratch.editor,self.final.editor): editor = self.final.editor
        term, ok = QInputDialog.getText(self,"Find","Text to find:")
        if ok and term:
            if not editor.find(term):
                cursor=editor.textCursor(); cursor.movePosition(cursor.MoveOperation.Start); editor.setTextCursor(cursor)
                if not editor.find(term): QMessageBox.information(self,"Find","Text not found.")

    def copy_calculator_result(self, result):
        QApplication.clipboard().setText(result); self.statusBar().showMessage("Calculator result copied to clipboard",2500)

    def toggle_theme(self):
        name = "light" if self.settings.value("theme","dark") == "dark" else "dark"
        self.settings.setValue("theme",name); apply_theme(QApplication.instance(),name)

    def about(self):
        QMessageBox.about(self,"About Lab Workspace","Lab Workspace v1\n\nLocal scratchpad, final document editor, revision history, and science calculator.\n\nVerify scientific calculations independently before operational use.")

    def closeEvent(self,event):
        self.autosave.stop(); self.save_both()
        self.settings.setValue("geometry",self.saveGeometry()); self.settings.setValue("windowState",self.saveState())
        self.settings.setValue("splitter",self.splitter.saveState()); event.accept()
