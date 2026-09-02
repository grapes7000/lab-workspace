DARK = """
QWidget { background:#202329; color:#e8eaed; font-size:13px; }
QMainWindow, QDialog { background:#17191d; }
QWidget#WorkPane { background:#262b31; border:1px solid #15191e; border-radius:1px; }
QWidget#PaneHeader { background:#30353c; border-top:1px solid #535b66; border-left:1px solid #4a525d; border-right:1px solid #171b20; border-bottom:1px solid #15191d; border-radius:1px; }
QPlainTextEdit, QTextBrowser, QLineEdit, QComboBox, QDoubleSpinBox, QListWidget, QTableWidget {
 background:#161a1f; border-top:1px solid #0c0f12; border-left:1px solid #0c0f12; border-right:1px solid #4a515b; border-bottom:1px solid #4a515b; border-radius:1px; padding:6px;
 selection-background-color:#315f8c;
}
QToolBar { background:#30353c; border-top:1px solid #535b66; border-bottom:1px solid #15191d; spacing:1px; padding:4px; }
QPushButton, QToolButton { background:#343940; border-top:1px solid #5a626d; border-left:1px solid #4e5661; border-right:1px solid #1a1e24; border-bottom:1px solid #13171c; border-radius:1px; padding:6px 10px; }
QPushButton:hover, QToolButton:hover { background:#3b424b; }
QPushButton:pressed, QToolButton:pressed { background:#272c33; border-top-color:#161a1f; border-left-color:#161a1f; border-right-color:#59616b; border-bottom-color:#59616b; }
QHeaderView::section { background:#343940; border-top:1px solid #5a626d; border-left:1px solid #4e5661; border-right:1px solid #1a1e24; border-bottom:1px solid #13171c; padding:5px; }
QLabel#PanelTitle { font-size:15px; font-weight:600; }
QDockWidget::title { background:#30353c; border-top:1px solid #535b66; border-left:1px solid #4a525d; border-right:1px solid #171b20; border-bottom:1px solid #15191d; padding:5px 7px; }
QStatusBar { background:#30353c; border-top:1px solid #535b66; }
QSplitter::handle { background:#30353c; }
QSplitter::handle:horizontal { width:3px; border-left:1px solid #535b66; border-right:1px solid #15191d; }
QSplitter::handle:vertical { height:3px; border-top:1px solid #535b66; border-bottom:1px solid #15191d; }
"""
LIGHT = """
QWidget { background:#e1e3e6; color:#1f2328; font-size:13px; }
QMainWindow, QDialog { background:#d4d7db; }
QWidget#WorkPane { background:#d8dade; border:1px solid #9aa1a9; border-radius:1px; }
QWidget#PaneHeader { background:#d2d5d9; border-top:1px solid #fafbfc; border-left:1px solid #f1f2f4; border-right:1px solid #9aa1a9; border-bottom:1px solid #858d96; border-radius:1px; }
QPlainTextEdit, QTextBrowser, QLineEdit, QComboBox, QDoubleSpinBox, QListWidget, QTableWidget {
 background:#fbfbfa; border-top:1px solid #9299a1; border-left:1px solid #9299a1; border-right:1px solid #ffffff; border-bottom:1px solid #ffffff; border-radius:1px; padding:6px;
 selection-background-color:#9cc9f0;
}
QToolBar { background:#d2d5d9; border-top:1px solid #fafbfc; border-bottom:1px solid #858d96; spacing:1px; padding:4px; }
QPushButton, QToolButton { background:#e0e2e5; border-top:1px solid #ffffff; border-left:1px solid #f6f7f8; border-right:1px solid #9aa1a9; border-bottom:1px solid #858d96; border-radius:1px; padding:6px 10px; }
QPushButton:hover, QToolButton:hover { background:#ebedef; }
QPushButton:pressed, QToolButton:pressed { background:#d2d5d9; border-top-color:#858d96; border-left-color:#858d96; border-right-color:#ffffff; border-bottom-color:#ffffff; }
QHeaderView::section { background:#e0e2e5; border-top:1px solid #ffffff; border-left:1px solid #f6f7f8; border-right:1px solid #9aa1a9; border-bottom:1px solid #858d96; padding:5px; }
QLabel#PanelTitle { font-size:15px; font-weight:600; }
QDockWidget::title { background:#d2d5d9; border-top:1px solid #fafbfc; border-left:1px solid #f1f2f4; border-right:1px solid #9aa1a9; border-bottom:1px solid #858d96; padding:5px 7px; }
QStatusBar { background:#d2d5d9; border-top:1px solid #fafbfc; }
QSplitter::handle { background:#d2d5d9; }
QSplitter::handle:horizontal { width:3px; border-left:1px solid #fafbfc; border-right:1px solid #858d96; }
QSplitter::handle:vertical { height:3px; border-top:1px solid #fafbfc; border-bottom:1px solid #858d96; }
"""


def apply_theme(app, name):
    app.setStyleSheet(LIGHT if name == "light" else DARK)
