DARK = """
QWidget { background:#17191d; color:#e8eaed; font-size:13px; }
QMainWindow, QDialog { background:#17191d; }
QPlainTextEdit, QLineEdit, QComboBox, QDoubleSpinBox, QListWidget, QTableWidget {
 background:#202329; border:1px solid #3a3f48; border-radius:2px; padding:6px;
 selection-background-color:#315f8c;
}
QToolBar { background:#202329; border-bottom:1px solid #343943; spacing:5px; padding:5px; }
QPushButton, QToolButton { background:#2b3038; border:1px solid #414852; border-radius:2px; padding:6px 10px; }
QPushButton:hover, QToolButton:hover { background:#363d47; }
QPushButton:pressed, QToolButton:pressed { background:#1f6aa5; }
QLabel#PanelTitle { font-size:15px; font-weight:600; }
QLabel#GhostText { color:#8d939d; background:#202329; border:1px dashed #3a3f48; border-radius:5px; padding:6px; }
QDockWidget::title { background:#202329; padding:7px; }
QStatusBar { background:#202329; }
QSplitter::handle { background:#343943; }
QMenuBar, QMenu { background:#202329; border:1px solid #343943; }
QMenu::item:selected { background:#363d47; }
QTabWidget::pane { border:1px solid #343943; }
QTabBar::tab { background:#202329; border:1px solid #343943; border-bottom:0; border-radius:2px 2px 0 0; padding:7px 13px; margin-right:2px; }
QTabBar::tab:selected { background:#2b3038; }
QHeaderView::section { background:#2b3038; border:1px solid #414852; padding:6px; }
"""
LIGHT = """
QWidget { background:#f5f6f8; color:#1f2328; font-size:13px; }
QPlainTextEdit, QLineEdit, QComboBox, QDoubleSpinBox, QListWidget, QTableWidget {
 background:white; border:1px solid #c7ccd4; border-radius:2px; padding:6px;
 selection-background-color:#9cc9f0;
}
QToolBar { background:#ffffff; border-bottom:1px solid #d8dce2; spacing:5px; padding:5px; }
QPushButton, QToolButton { background:#ffffff; border:1px solid #c7ccd4; border-radius:2px; padding:6px 10px; }
QPushButton:hover, QToolButton:hover { background:#edf2f7; }
QLabel#PanelTitle { font-size:15px; font-weight:600; }
QLabel#GhostText { color:#727881; background:#f0f1f3; border:1px dashed #c7ccd4; border-radius:5px; padding:6px; }
QDockWidget::title { background:#ffffff; padding:7px; }
QStatusBar { background:#ffffff; }
QSplitter::handle { background:#c7ccd4; }
QMenuBar, QMenu { background:#ffffff; border:1px solid #d8dce2; }
QMenu::item:selected { background:#edf2f7; }
QTabWidget::pane { border:1px solid #d8dce2; }
QTabBar::tab { background:#ffffff; border:1px solid #c7ccd4; border-bottom:0; border-radius:2px 2px 0 0; padding:7px 13px; margin-right:2px; }
QTabBar::tab:selected { background:#edf2f7; }
QHeaderView::section { background:#ffffff; border:1px solid #c7ccd4; padding:6px; }
"""


def apply_theme(app, name):
    app.setStyleSheet(LIGHT if name == "light" else DARK)
