from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QSplitter,QPlainTextEdit,QTextBrowser,QTabWidget,QHBoxLayout,QPushButton,QFileDialog
class WritingPage(QWidget):
 def __init__(self,db,parent=None):
  super().__init__(parent);self.db=db;layout=QVBoxLayout(self);split=QSplitter(Qt.Orientation.Vertical)
  self.scratch=QPlainTextEdit(db.doc('scratchpad'));self.scratch.setPlaceholderText('Scratchpad: temporary notes are autosaved into append-only history.')
  tabs=QTabWidget();self.final=QPlainTextEdit(db.doc('final'));self.preview=QTextBrowser();self.side=QSplitter();self.side_edit=QPlainTextEdit(self.final.toPlainText());self.side_preview=QTextBrowser();self.side.addWidget(self.side_edit);self.side.addWidget(self.side_preview)
  tabs.addTab(self.final,'Edit');tabs.addTab(self.preview,'Preview');tabs.addTab(self.side,'Side by Side');split.addWidget(self.scratch);split.addWidget(tabs);layout.addWidget(split)
  self.sync=False;self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(700);self.timer.timeout.connect(self.save)
  self.scratch.textChanged.connect(self.timer.start);self.final.textChanged.connect(lambda:self.changed(self.final,self.side_edit));self.side_edit.textChanged.connect(lambda:self.changed(self.side_edit,self.final));tabs.currentChanged.connect(lambda _:self.render())
 def changed(self,source,target):
  if self.sync:return
  self.sync=True;target.setPlainText(source.toPlainText());self.sync=False;self.render();self.timer.start()
 def render(self):self.preview.setMarkdown(self.final.toPlainText());self.side_preview.setMarkdown(self.final.toPlainText())
 def save(self):self.db.save_doc('scratchpad',self.scratch.toPlainText());self.db.save_doc('final',self.final.toPlainText())
 def append_markdown(self,text):self.final.appendPlainText('\n'+text);self.render()
