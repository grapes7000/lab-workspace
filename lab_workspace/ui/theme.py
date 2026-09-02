LIGHT = """
QWidget { background:#F5F5F6; color:#292B2F; font-size:13px; }
QMainWindow, QDialog { background:#F5F5F6; }
QWidget#WorkPane { background:#FFFFFF; border:0; border-radius:0; }
QWidget#PaneHeader { background:#FFFFFF; border:0; border-bottom:1px solid #D3D4D7; border-radius:0; }
QPlainTextEdit, QTextBrowser, QLineEdit, QComboBox, QDoubleSpinBox, QListWidget, QTableWidget {
 background:#FFFFFF; border:1px solid #D0D1D4; border-radius:3px; padding:6px;
 selection-background-color:#B9D8F2;
}
QToolBar { background:#F1F1F2; border:0; border-bottom:1px solid #D3D4D7; spacing:1px; padding:4px; }
QPushButton, QToolButton {
 background:#F1F1F2; border-top:1px solid #FAFAFB; border-left:1px solid #FAFAFB;
 border-right:1px solid #D1D2D5; border-bottom:1px solid #D1D2D5; border-radius:4px; padding:6px 10px;
}
QPushButton:hover, QToolButton:hover { background:#F8F8F9; }
QPushButton:pressed, QToolButton:pressed {
 background:#ECEDEF; border-top-color:#D1D2D5; border-left-color:#D1D2D5;
 border-right-color:#FAFAFB; border-bottom-color:#FAFAFB; padding:7px 9px 5px 11px;
}
QHeaderView::section { background:#F0F0F1; border:0; border-right:1px solid #D3D4D7; border-bottom:1px solid #D3D4D7; padding:5px; }
QLabel#PanelTitle { font-size:15px; font-weight:600; background:transparent; }
QDockWidget::title { background:#F1F1F2; border:0; border-bottom:1px solid #D3D4D7; padding:5px 7px; }
QStatusBar, QMenuBar { background:#F5F5F6; border:0; border-top:1px solid #D3D4D7; }
QMenu { background:#FFFFFF; border:1px solid #D3D4D7; }
QMenu::item:selected { background:#F1F1F2; }
QSplitter::handle { background:#D3D4D7; }
QSplitter::handle:horizontal { width:2px; }
QSplitter::handle:vertical { height:2px; }
"""

DARK = """
QWidget { background:#202124; color:#ECEEF1; font-size:13px; }
QMainWindow, QDialog { background:#202124; }
QWidget#WorkPane { background:#25262A; border:0; border-radius:0; }
QWidget#PaneHeader { background:#25262A; border:0; border-bottom:1px solid #414349; border-radius:0; }
QPlainTextEdit, QTextBrowser, QLineEdit, QComboBox, QDoubleSpinBox, QListWidget, QTableWidget {
 background:#2A2B2F; border:1px solid #46484E; border-radius:3px; padding:6px;
 selection-background-color:#315F8C;
}
QToolBar { background:#25262A; border:0; border-bottom:1px solid #414349; spacing:1px; padding:4px; }
QPushButton, QToolButton {
 background:#303136; border-top:1px solid #3C3E44; border-left:1px solid #3C3E44;
 border-right:1px solid #222328; border-bottom:1px solid #222328; border-radius:4px; padding:6px 10px;
}
QPushButton:hover, QToolButton:hover { background:#383A40; }
QPushButton:pressed, QToolButton:pressed {
 background:#2B2C31; border-top-color:#222328; border-left-color:#222328;
 border-right-color:#3C3E44; border-bottom-color:#3C3E44; padding:7px 9px 5px 11px;
}
QHeaderView::section { background:#2F3035; border:0; border-right:1px solid #414349; border-bottom:1px solid #414349; padding:5px; }
QLabel#PanelTitle { font-size:15px; font-weight:600; background:transparent; }
QDockWidget::title { background:#25262A; border:0; border-bottom:1px solid #414349; padding:5px 7px; }
QStatusBar, QMenuBar { background:#202124; border:0; border-top:1px solid #414349; }
QMenu { background:#2A2B2F; border:1px solid #414349; }
QMenu::item:selected { background:#35363B; }
QSplitter::handle { background:#414349; }
QSplitter::handle:horizontal { width:2px; }
QSplitter::handle:vertical { height:2px; }
"""


def apply_theme(app, name):
    app.setStyleSheet(DARK if name == "dark" else LIGHT)
