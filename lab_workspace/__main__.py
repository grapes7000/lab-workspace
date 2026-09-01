import sys
from PySide6.QtWidgets import QApplication
from lab_workspace.data.database import Database
from lab_workspace.ui.main_window import MainWindow
from lab_workspace.ui.theme import apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Lab Workspace")
    app.setOrganizationName("Local Lab Tools")
    app.setStyle("Fusion")
    database = Database()
    window = MainWindow(database)
    apply_theme(app, window.settings.value("theme", "dark"))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
