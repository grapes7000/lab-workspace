from PySide6.QtWidgets import QDialog,QFormLayout,QLineEdit,QComboBox,QDoubleSpinBox,QDialogButtonBox,QVBoxLayout

def spin(nullable=True):
 s=QDoubleSpinBox();s.setRange(0,1e12);s.setDecimals(8);s.setSpecialValueText("blank" if nullable else "0");s.setValue(0);return s
class RecordDialog(QDialog):
 def __init__(self,title,fields,parent=None):
  super().__init__(parent);self.setWindowTitle(title);self.resize(500,500);layout=QVBoxLayout(self);form=QFormLayout();self.widgets={}
  for key,label,kind,choices in fields:
   if kind=='combo':w=QComboBox();w.addItems(choices)
   elif kind=='number':w=spin()
   else:w=QLineEdit()
   self.widgets[key]=w;form.addRow(label,w)
  layout.addLayout(form);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
 def values(self):
  d={}
  for k,w in self.widgets.items():
   if isinstance(w,QComboBox):d[k]=w.currentText()
   elif isinstance(w,QDoubleSpinBox):d[k]=None if w.value()==w.minimum() else w.value()
   else:d[k]=w.text().strip()
  return d
