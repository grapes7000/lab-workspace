from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QPushButton,QTableWidget,QTableWidgetItem,QTabWidget,QFileDialog,QMessageBox
from lab_workspace.ui.common import RecordDialog
from lab_workspace.data.excel_io import export_workbook,import_sheet
MAT_FIELDS=[('name','Name*','text',[]),('formula','Formula','text',[]),('mw','Molar mass (g/mol)','number',[]),('density','Density','number',[]),('density_unit','Density unit','combo',['g/mL','g/L','kg/L','mg/mL']),('form','Form','combo',['Neat solid','Neat liquid','Solution','Mixture','Other']),('purity','Purity %','number',[]),('active_fraction','Active fraction %','number',[]),('aliases','Aliases','text',[]),('tags','Tags','text',[]),('notes','Notes','text',[])]
SAMPLE_FIELDS=[('name','Sample name*','text',[]),('sample_type','Type','combo',['Gasoline','Diesel','Jet fuel','Fuel blend','Additive','Reference material','Field sample','Unknown','Other']),('project','Project','text',[]),('status','Status','combo',['Registered','Testing Requested','Testing in Progress','Awaiting Review','Completed','Disposed']),('source','Source','text',[]),('collection_location','Collection location','text',[]),('collection_date','Collection date','text',[]),('received_date','Received date','text',[]),('fuel_grade','Fuel grade','text',[]),('nominal_ethanol','Nominal ethanol %','number',[]),('lot_number','Lot/batch','text',[]),('quantity','Quantity','number',[]),('quantity_unit','Quantity unit','combo',['mL','L','g','kg']),('container','Container','text',[]),('storage_location','Storage location','text',[]),('parent_sample_code','Parent sample code','text',[]),('tags','Tags','text',[]),('notes','Notes','text',[])]
class LibraryPage(QWidget):
 def __init__(self,db,parent=None):
  super().__init__(parent);self.db=db;layout=QVBoxLayout(self);bar=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText('Search materials or samples...');bar.addWidget(self.search)
  for label,fn in [('Add Material',self.add_material),('Add Sample',self.add_sample),('Import CSV',self.import_csv),('Export CSV',self.export_csv),('Import XLSX',self.import_xlsx),('Export XLSX',self.export_xlsx)]:b=QPushButton(label);b.clicked.connect(fn);bar.addWidget(b)
  layout.addLayout(bar);self.tabs=QTabWidget();self.materials=QTableWidget();self.samples=QTableWidget();self.tabs.addTab(self.materials,'Materials');self.tabs.addTab(self.samples,'Samples');layout.addWidget(self.tabs);self.search.textChanged.connect(self.refresh);self.tabs.currentChanged.connect(self.refresh);self.refresh()
 def fill(self,table,rows,cols):
  table.setColumnCount(len(cols));table.setHorizontalHeaderLabels(cols);table.setRowCount(len(rows))
  for r,row in enumerate(rows):
   for c,key in enumerate(cols):table.setItem(r,c,QTableWidgetItem(str(row[key] if row[key] is not None else '')))
  table.resizeColumnsToContents()
 def refresh(self,*_):
  term=self.search.text();self.fill(self.materials,self.db.search('materials',term),['code','name','formula','mw','density','density_unit','form','purity','active_fraction']);self.fill(self.samples,self.db.search('samples',term),['code','name','sample_type','project','status','fuel_grade','lot_number','quantity','quantity_unit','storage_location'])
 def add_material(self):
  d=RecordDialog('Add Material',MAT_FIELDS,self)
  if d.exec() and d.values()['name']:self.db.save_material(d.values());self.refresh()
 def add_sample(self):
  d=RecordDialog('Add Sample',SAMPLE_FIELDS,self)
  if d.exec() and d.values()['name']:self.db.save_sample(d.values());self.refresh()
 def kind(self):return 'materials' if self.tabs.currentIndex()==0 else 'samples'
 def import_csv(self):
  p,_=QFileDialog.getOpenFileName(self,'Import CSV','','CSV (*.csv)')
  if p:
   a,s,w=self.db.import_csv(self.kind(),p);QMessageBox.information(self,'Import',f'{a} added/updated; {s} skipped\n'+'\n'.join(w[:5]));self.refresh()
 def export_csv(self):
  p,_=QFileDialog.getSaveFileName(self,'Export CSV',f'{self.kind()}.csv','CSV (*.csv)')
  if p:QMessageBox.information(self,'Export',f'{self.db.export_csv(self.kind(),p)} rows exported')
 def export_xlsx(self):
  p,_=QFileDialog.getSaveFileName(self,'Export Workbook','lab_workspace_library.xlsx','Excel (*.xlsx)')
  if p:export_workbook(self.db,p)
 def import_xlsx(self):
  p,_=QFileDialog.getOpenFileName(self,'Import Workbook','','Excel (*.xlsx)')
  if p:
   a,s,w=import_sheet(self.db,p,self.kind());QMessageBox.information(self,'Import',f'{a} added/updated; {s} skipped\n'+'\n'.join(w[:5]));self.refresh()
