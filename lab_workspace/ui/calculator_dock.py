from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QComboBox, QDoubleSpinBox, QFormLayout, QTabWidget, QMessageBox
)
from lab_workspace.core.calculator import (
    evaluate, format_number, mass_from_moles, moles_from_mass, molarity,
    dilution_final_volume, ppm_mass
)


class CalculatorDock(QDockWidget):
    result_ready = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Science Calculator", parent)
        self.setObjectName("calculatorDock")
        self.setMinimumWidth(280)
        tabs = QTabWidget(); tabs.addTab(self.expression_widget(), "Scientific")
        tabs.addTab(self.quick_widget(), "Lab Quick Calc")
        self.setWidget(tabs)

    def expression_widget(self):
        panel = QWidget(); layout = QVBoxLayout(panel)
        self.expression = QLineEdit(); self.expression.setPlaceholderText("Example: sqrt(25) + sin(pi/2)")
        self.expression.returnPressed.connect(self.calculate_expression)
        self.expression_result = QLabel("Result: ")
        calculate = QPushButton("Calculate"); calculate.clicked.connect(self.calculate_expression)
        layout.addWidget(QLabel("Operators: + - * / ^ %\nFunctions: sqrt, sin, cos, tan, log, ln, exp, abs\nConstants: pi, e, tau"))
        layout.addWidget(self.expression); layout.addWidget(calculate); layout.addWidget(self.expression_result); layout.addStretch()
        return panel

    def calculate_expression(self):
        try:
            result = format_number(evaluate(self.expression.text()))
            self.expression_result.setText("Result: " + result); self.result_ready.emit(result)
        except Exception as error:
            QMessageBox.warning(self, "Calculation Error", str(error))

    def spin(self):
        box = QDoubleSpinBox(); box.setDecimals(9); box.setRange(-1e12, 1e12); box.setSingleStep(1.0)
        return box

    def quick_widget(self):
        panel = QWidget(); layout = QVBoxLayout(panel); form = QFormLayout()
        self.mode = QComboBox(); self.mode.addItems([
            "Mass from moles", "Moles from mass", "Molarity",
            "Dilution final volume", "ppm by mass"
        ])
        self.a, self.b, self.c = self.spin(), self.spin(), self.spin()
        self.label_a, self.label_b, self.label_c = QLabel(), QLabel(), QLabel()
        form.addRow("Calculation", self.mode); form.addRow(self.label_a, self.a)
        form.addRow(self.label_b, self.b); form.addRow(self.label_c, self.c)
        self.quick_result = QLabel("Result: ")
        button = QPushButton("Calculate"); button.clicked.connect(self.calculate_quick)
        self.mode.currentIndexChanged.connect(self.update_labels)
        layout.addLayout(form); layout.addWidget(button); layout.addWidget(self.quick_result); layout.addStretch()
        self.update_labels(); return panel

    def update_labels(self):
        labels = [
            ("Moles", "Molecular weight (g/mol)", "Unused"),
            ("Mass (g)", "Molecular weight (g/mol)", "Unused"),
            ("Moles", "Volume (L)", "Unused"),
            ("C1", "V1", "C2"),
            ("Solute mass (mg)", "Solution mass (kg)", "Unused"),
        ][self.mode.currentIndex()]
        for label, text in zip((self.label_a, self.label_b, self.label_c), labels): label.setText(text)
        self.c.setVisible(self.mode.currentIndex() == 3); self.label_c.setVisible(self.mode.currentIndex() == 3)

    def calculate_quick(self):
        try:
            i, a, b, c = self.mode.currentIndex(), self.a.value(), self.b.value(), self.c.value()
            functions = [
                lambda: (mass_from_moles(a,b), "g"), lambda: (moles_from_mass(a,b), "mol"),
                lambda: (molarity(a,b), "mol/L"), lambda: (dilution_final_volume(a,b,c), "same volume unit as V1"),
                lambda: (ppm_mass(a,b), "mg/kg (ppm)"),
            ]
            value, unit = functions[i](); result = f"{format_number(value)} {unit}"
            self.quick_result.setText("Result: " + result); self.result_ready.emit(result)
        except Exception as error:
            QMessageBox.warning(self, "Calculation Error", str(error))
