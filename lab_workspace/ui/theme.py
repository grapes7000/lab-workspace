DARK = """
QWidget { background:#17191d; color:#e8eaed; font-size:13px; }
QMainWindow, QDialog { background:#17191d; }
QPlainTextEdit, QLineEdit, QComboBox, QDoubleSpinBox, QListWidget {
 background:#202329; border:1px solid #3a3f48; border-radius:6px; padding:6px;
 selection-background-color:#315f8c;
}
QToolBar { background:#202329; border-bottom:1px solid #343943; spacing:5px; padding:5px; }
QPushButton, QToolButton { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #353c46,stop:0.5 #2d333c,stop:1 #252a31); border-top:1px solid #59616d; border-left:1px solid #4b535e; border-right:1px solid #1c2026; border-bottom:1px solid #15191e; border-radius:6px; padding:6px 10px; }
QPushButton:hover, QToolButton:hover { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #414956,stop:.5 #353c46,stop:1 #2b3038); }
QPushButton:pressed, QToolButton:pressed { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #255477,stop:1 #1f6aa5); border-top:1px solid #1a415f; border-left:1px solid #1a415f; border-right:1px solid #4a86b0; border-bottom:1px solid #4a86b0; }
QTabBar::tab { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #303640,stop:1 #22272e); border-top:1px solid #505966; border-left:1px solid #424a55; border-right:1px solid #1b1f25; border-bottom:1px solid #15191d; border-radius:6px 6px 0 0; padding:7px 13px; margin-right:2px; }
QTabBar::tab:selected { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #3b434e,stop:1 #2b3038); border-bottom-color:#2b3038; }
QLabel#PanelTitle { font-size:15px; font-weight:600; }
QLabel#GhostText { color:#8d939d; background:#202329; border:1px dashed #3a3f48; border-radius:5px; padding:6px; }
QDockWidget::title { background:#202329; padding:7px; }
QStatusBar { background:#202329; }
QSplitter::handle { background:#343943; }
"""
LIGHT = """
QWidget { background:#f5f6f8; color:#1f2328; font-size:13px; }
QPlainTextEdit, QLineEdit, QComboBox, QDoubleSpinBox, QListWidget {
 background:white; border:1px solid #c7ccd4; border-radius:6px; padding:6px;
 selection-background-color:#9cc9f0;
}
QToolBar { background:#ffffff; border-bottom:1px solid #d8dce2; spacing:5px; padding:5px; }
QPushButton, QToolButton { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:0.5 #f7f8fa,stop:1 #e8ebef); border-top:1px solid #ffffff; border-left:1px solid #e1e5ea; border-right:1px solid #aeb6c0; border-bottom:1px solid #969faa; border-radius:6px; padding:6px 10px; }
QPushButton:hover, QToolButton:hover { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #dde8f3); }
QPushButton:pressed, QToolButton:pressed { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #d8e3ef,stop:1 #f4f7fa); border-top:1px solid #aeb6c0; border-left:1px solid #aeb6c0; border-right:1px solid #ffffff; border-bottom:1px solid #ffffff; }
QTabBar::tab { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #e8ebef); border-top:1px solid #ffffff; border-left:1px solid #d8dde4; border-right:1px solid #afb7c1; border-bottom:1px solid #969faa; border-radius:6px 6px 0 0; padding:7px 13px; margin-right:2px; }
QTabBar::tab:selected { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #f5f6f8); border-bottom-color:#f5f6f8; }
QLabel#PanelTitle { font-size:15px; font-weight:600; }
QLabel#GhostText { color:#727881; background:#f0f1f3; border:1px dashed #c7ccd4; border-radius:5px; padding:6px; }
QDockWidget::title { background:#ffffff; padding:7px; }
QStatusBar { background:#ffffff; }
QSplitter::handle { background:#c7ccd4; }
"""


def apply_theme(app, name):
    app.setStyleSheet(LIGHT if name == "light" else DARK)
