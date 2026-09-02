import json
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QPushButton,QTableWidget,QTableWidgetItem,QDialog,QFormLayout,QComboBox,QDialogButtonBox,QMessageBox
class TestingPage(QWidget):
 def __init__(self,db,parent=None):
  super().__init__(parent);self.db=db;layout=QVBoxLayout(self);bar=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText('Search requests by sample, method, status, assignee...');bar.addWidget(self.search)
  add=QPushButton('Request Test');add.clicked.connect(self.request);result=QPushButton('Enter Result');result.clicked.connect(self.result);bar.addWidget(add);bar.addWidget(result);layout.addLayout(bar);self.table=QTableWidget();layout.addWidget(self.table);self.search.textChanged.connect(self.refresh);self.refresh()
 def refresh(self,*_):
  rows=self.db.search('test_requests',self.search.text());cols=['code','sample_code','method_code','status','priority','assigned_to','due_date','notes'];self.table.setColumnCount(len(cols));self.table.setHorizontalHeaderLabels(cols);self.table.setRowCount(len(rows))
  for r,row in enumerate(rows):
   for c,k in enumerate(cols):self.table.setItem(r,c,QTableWidgetItem(str(row[k] or '')))
  self.table.resizeColumnsToContents()
 def request(self):
  samples=self.db.search('samples','');methods=self.db.methods()
  if not samples:QMessageBox.warning(self,'No Samples','Add a sample first.');return
  d=QDialog(self);d.setWindowTitle('Request Test');f=QFormLayout(d);sample=QComboBox();sample.addItems([r['code']+' | '+r['name'] for r in samples]);method=QComboBox();method.addItems([r['code']+' | '+r['name'] for r in methods]);priority=QComboBox();priority.addItems(['Low','Normal','High']);assignee=QLineEdit();due=QLineEdit();notes=QLineEdit()
  for label,w in [('Sample',sample),('Method',method),('Priority',priority),('Assigned to',assignee),('Due date',due),('Notes',notes)]:f.addRow(label,w)
  buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(d.accept);buttons.rejected.connect(d.reject);f.addRow(buttons)
  if d.exec():self.db.save_request({'sample_code':sample.currentText().split(' | ')[0],'method_code':method.currentText().split(' | ')[0],'priority':priority.currentText(),'assigned_to':assignee.text(),'due_date':due.text(),'notes':notes.text()});self.refresh()
 def result(self):
  row=self.table.currentRow()
  if row<0:QMessageBox.warning(self,'Select Request','Select a test request first.');return
  request=self.table.item(row,0).text();method_code=self.table.item(row,2).text();method=next(x for x in self.db.methods() if x['code']==method_code);fields=json.loads(method['fields_json']);d=QDialog(self);d.setWindowTitle('Enter Test Result');form=QFormLayout(d);inputs=[]
  for field in fields:
   w=QLineEdit();w.setPlaceholderText(field.get('unit',''));form.addRow(field['name'],w);inputs.append((field,w))
  operator=QLineEdit();instrument=QLineEdit();notes=QLineEdit();form.addRow('Operator',operator);form.addRow('Instrument',instrument);form.addRow('Notes',notes);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(d.accept);buttons.rejected.connect(d.reject);form.addRow(buttons)
  while d.exec():
   values=[]
   invalid=[]
   for field,w in inputs:
    text=w.text().strip();v={'field_key':field['key'],'unit':field.get('unit','')}
    if field['type']=='number':
     try:v['numeric_value']=float(text)
     except ValueError:invalid.append(field['name'])
    else:v['text_value']=text
    values.append(v)
   if invalid:
    QMessageBox.warning(d,'Invalid numeric result',f"Enter numeric values for: {', '.join(invalid)}")
    continue
   run=self.db.save_run(request,method_code,values,{'operator':operator.text(),'instrument':instrument.text(),'notes':notes.text()});QMessageBox.information(self,'Saved',f'Result saved as {run}')
   return
