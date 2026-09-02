import json
from dataclasses import asdict
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QPushButton,QTableWidget,QTableWidgetItem,QPlainTextEdit,QLabel,QMessageBox,QHeaderView
from lab_workspace.core.chemistry import Species,calculate_reaction
COLS=['Name','Formula','Coeff','MW g/mol','Mass','Mass unit','Volume','Volume unit','Density','Density unit','Moles','Amount unit','Purity %','Actual yield g']
class StoichiometryPage(QWidget):
 def __init__(self,db,writing,parent=None):
  super().__init__(parent);self.db=db;self.writing=writing;self.last_markdown='';layout=QVBoxLayout(self);top=QHBoxLayout();self.title=QLineEdit();self.title.setPlaceholderText('Reaction or calculation title');top.addWidget(self.title)
  for label,fn in [('Add Reactant',lambda:self.add('reactant')),('Add Product',lambda:self.add('product')),('Remove Row',self.remove),('Calculate All',self.calculate),('Save Calculation',self.save),('Append to Final',self.append_final)]:b=QPushButton(label);b.clicked.connect(fn);top.addWidget(b)
  layout.addLayout(top);self.table=QTableWidget(0,len(COLS));self.table.setHorizontalHeaderLabels(COLS);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);layout.addWidget(self.table);self.result=QPlainTextEdit();self.result.setReadOnly(True);layout.addWidget(QLabel('Results and calculation trace'));layout.addWidget(self.result);self.add('reactant');self.add('product')
 def add(self,side):
  r=self.table.rowCount();self.table.insertRow(r);name=QTableWidgetItem('');name.setData(256,side);self.table.setItem(r,0,name)
  defaults=['','1','','','g','','mL','','g/mL','','mol','100','']
  for c,v in enumerate(defaults,1):self.table.setItem(r,c,QTableWidgetItem(v))
  self.table.item(r,0).setToolTip(side.title())
 def remove(self):
  for r in sorted({i.row() for i in self.table.selectedIndexes()},reverse=True):self.table.removeRow(r)
 def val(self,r,c):
  t=self.table.item(r,c).text().strip() if self.table.item(r,c) else ''
  return float(t) if t else None
 def species(self):
  out=[]
  for r in range(self.table.rowCount()):
   item=self.table.item(r,0);side=item.data(256) if item else 'reactant'
   out.append(Species(side=side,name=item.text().strip(),formula=self.table.item(r,1).text().strip(),coefficient=self.val(r,2) or 1,mw=self.val(r,3),mass=self.val(r,4),mass_unit=self.table.item(r,5).text().strip() or 'g',volume=self.val(r,6),volume_unit=self.table.item(r,7).text().strip() or 'mL',density=self.val(r,8),density_unit=self.table.item(r,9).text().strip() or 'g/mL',moles=self.val(r,10),amount_unit=self.table.item(r,11).text().strip() or 'mol',purity=self.val(r,12) if self.val(r,12) is not None else 100,actual_yield=self.val(r,13)))
  return out
 def calculate(self):
  try:s=self.species();res=calculate_reaction(s)
  except Exception as e:QMessageBox.warning(self,'Calculation Error',str(e));return
  lines=[f"# {self.title.text().strip() or 'Stoichiometry Calculation'}","",f"- Balanced: {'Yes' if res.balanced else 'No'}",f"- Limiting reagent: {res.limiting or 'Insufficient data'}",f"- Reaction extent: {res.extent if res.extent is not None else 'Insufficient data'} mol-reaction","","## Species"]
  for row in res.rows:
   lines.append(f"- **{row['name'] or row['formula'] or 'Unnamed'}** ({row['side']}): MW={fmt(row['mw'])} g/mol; mass={fmt(row['mass_g'])} g; volume={fmt(row['volume_L'])} L; moles={fmt(row['moles'])} mol; theoretical={fmt(row['theoretical_moles'])} mol; remaining={fmt(row['remaining_moles'])} mol; theoretical mass={fmt(row['theoretical_mass_g'])} g")
  if res.warnings:lines+=['','## Warnings']+[f'- {w}' for w in res.warnings]
  lines+=['','> Verify this calculation independently before laboratory use.'];self.last_markdown='\n'.join(lines);self.result.setPlainText(self.last_markdown)
  self.last=(s,res)
 def save(self):
  if not self.last_markdown:self.calculate()
  if not self.last_markdown:return
  s,res=self.last;self.db.save_calculation(self.title.text() or 'Stoichiometry Calculation',[asdict(x) for x in s],asdict(res),self.last_markdown);QMessageBox.information(self,'Saved','Immutable calculation record saved.')
 def append_final(self):
  if not self.last_markdown:self.calculate()
  if self.last_markdown:self.writing.append_markdown(self.last_markdown)
def fmt(x):return '—' if x is None else f'{x:.8g}'
