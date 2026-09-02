import sys

from PySide6.QtWidgets import QApplication

from lab_workspace.data.database import Database
from lab_workspace.ui.main_window import MainWindow
from lab_workspace.ui.safe_docking import install_safe_tool_host


# QDockWidget must remain a QMainWindow-managed wrapper. Install the safe tool
# host methods before MainWindow is instantiated so only dock contents are moved
# into the center work area.
install_safe_tool_host(MainWindow)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Lab Workspace")
    app.setStyle("Fusion")
    window = MainWindow(Database())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
