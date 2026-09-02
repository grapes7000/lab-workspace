import sys
from PySide6.QtWidgets import QApplication
from lab_workspace.data.database import Database
from lab_workspace.ui.main_window import MainWindow
def main():
 app=QApplication(sys.argv);app.setApplicationName('Lab Workspace');app.setStyle('Fusion');window=MainWindow(Database());window.show();return app.exec()
if __name__=='__main__':raise SystemExit(main())
