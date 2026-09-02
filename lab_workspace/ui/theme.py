LIGHT = """
QWidget { background:#F5F5F6; color:#292B2F; font-size:13px; }
QMainWindow, QDialog { background:#F5F5F6; }
QWidget#WorkPane { background:#FFFFFF; border:0; border-radius:0; }
QWidget#PaneHeader { background:#FFFFFF; border:0; border-bottom:1px solid #D3D4D7; border-radius:0; }
QWidget#CenterHost, QWidget#CenterPaneContent { background:#FFFFFF; }
QWidget#CenterControls, QWidget#CenterPaneHeader { background:#F1F1F2; border:0; border-bottom:1px solid #D3D4D7; }
QLabel#CenterControlsTitle, QLabel#CenterPaneLabel, QLabel#ExplorerTitle { font-size:11px; font-weight:700; letter-spacing:1px; }
QLabel#CenterPaneEmpty, QLabel#ExplorerHint { color:#72757B; background:transparent; padding:8px; }
QWidget#WorkspaceExplorer { background:#F7F7F8; }
QTreeWidget { background:#F7F7F8; border:0; padding:2px; }
QTreeWidget::item { min-height:24px; border-radius:3px; }
QTreeWidget::item:hover { background:#E8E9EB; }
QTreeWidget::item:selected { background:#DDE8F2; color:#202226; }
QPlainTextEdit, QTextBrowser, QLineEdit, QComboBox, QDoubleSpinBox, QListWidget, QTableWidget {
 background:#FFFFFF; border:1px solid #D0D1D4; border-radius:3px; padding:6px;
 selection-background-color:#B9D8F2;
}
QToolBar { background:#F1F1F2; border:0; border-bottom:1px solid #D3D4D7; spacing:1px; padding:4px; }
QToolBar#ActivityRail { background:#E9EAEC; border:0; border-right:1px solid #CBCDD1; spacing:3px; padding:4px 3px; }
QToolBar#ActivityRail QToolButton { border-radius:4px; padding:7px; min-width:28px; min-height:28px; }
QToolBar#ActivityRail QToolButton:hover { background:#DCDDE0; }
QPushButton, QToolButton {
 background:transparent; border:1px solid transparent; border-bottom:0;
 border-radius:4px 4px 0 0; padding:7px 10px;
}
QPushButton:hover, QToolButton:hover {
 background:#E1E2E5; border-top-color:#D1D2D5; border-left-color:#D1D2D5; border-right-color:#D1D2D5;
}
QPushButton:pressed, QToolButton:pressed {
 background:#D7D8DB; border-top-color:#C5C6C9; border-left-color:#C5C6C9; border-right-color:#C5C6C9;
 padding:8px 9px 6px 11px;
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
QWidget#CenterHost, QWidget#CenterPaneContent { background:#25262A; }
QWidget#CenterControls, QWidget#CenterPaneHeader { background:#222327; border:0; border-bottom:1px solid #414349; }
QLabel#CenterControlsTitle, QLabel#CenterPaneLabel, QLabel#ExplorerTitle { font-size:11px; font-weight:700; letter-spacing:1px; }
QLabel#CenterPaneEmpty, QLabel#ExplorerHint { color:#9A9DA4; background:transparent; padding:8px; }
QWidget#WorkspaceExplorer { background:#222327; }
QTreeWidget { background:#222327; border:0; padding:2px; }
QTreeWidget::item { min-height:24px; border-radius:3px; }
QTreeWidget::item:hover { background:#303136; }
QTreeWidget::item:selected { background:#313E4B; color:#F0F2F5; }
QPlainTextEdit, QTextBrowser, QLineEdit, QComboBox, QDoubleSpinBox, QListWidget, QTableWidget {
 background:#2A2B2F; border:1px solid #46484E; border-radius:3px; padding:6px;
 selection-background-color:#315F8C;
}
QToolBar { background:#25262A; border:0; border-bottom:1px solid #414349; spacing:1px; padding:4px; }
QToolBar#ActivityRail { background:#1B1C1F; border:0; border-right:1px solid #414349; spacing:3px; padding:4px 3px; }
QToolBar#ActivityRail QToolButton { border-radius:4px; padding:7px; min-width:28px; min-height:28px; }
QToolBar#ActivityRail QToolButton:hover { background:#303136; }
QPushButton, QToolButton {
 background:transparent; border:1px solid transparent; border-bottom:0;
 border-radius:4px 4px 0 0; padding:7px 10px;
}
QPushButton:hover, QToolButton:hover {
 background:#383A40; border-top-color:#4A4C52; border-left-color:#4A4C52; border-right-color:#4A4C52;
}
QPushButton:pressed, QToolButton:pressed {
 background:#303136; border-top-color:#24252A; border-left-color:#24252A; border-right-color:#24252A;
 padding:8px 9px 6px 11px;
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
