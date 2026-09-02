from PySide6.QtWidgets import QMainWindow,QTabWidget,QMessageBox
from lab_workspace.ui.writing import WritingPage
from lab_workspace.ui.library import LibraryPage
from lab_workspace.ui.stoichiometry import StoichiometryPage
from lab_workspace.ui.testing import TestingPage
class MainWindow(QMainWindow):
 def __init__(self,db):
  super().__init__();self.db=db;self.setWindowTitle('Lab Workspace v1.2');self.resize(1500,900);tabs=QTabWidget();self.writing=WritingPage(db);tabs.addTab(self.writing,'Writing Workspace');tabs.addTab(LibraryPage(db),'Materials and Samples');tabs.addTab(StoichiometryPage(db,self.writing),'Stoichiometry');tabs.addTab(TestingPage(db),'Testing');self.setCentralWidget(tabs);self.statusBar().showMessage('Local database ready')
  help_menu=self.menuBar().addMenu('Help');help_menu.addAction('About',lambda:QMessageBox.about(self,'About','Lab Workspace v1.2\nMaterials, samples, testing, stoichiometry, and Markdown writing.\n\nNot validated. Verify calculations and results independently.'))
 def closeEvent(self,event):self.writing.save();event.accept()
