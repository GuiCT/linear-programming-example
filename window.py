
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog, QLabel, QVBoxLayout, QTableWidget, QHeaderView, QWidget, QTableWidgetItem, QSpinBox, QHBoxLayout, QPushButton, QErrorMessage
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox
from ortools.linear_solver import pywraplp

ABOUT_TEXT = '''
<h1>
    Programação Linear
</h1>

<h2>
    Problema de otimização de média
</h2>

Calcula a melhor média possível dados:
<ul>
    <li>Peso de cada atividade</li>
    <li>Nota obtida a cada hora de estudo semanal</li>
    <li>Tempo de estudo semanal disponível</li>
</ul>

<p>
    Desenvolvido por: Guilherme Cesar Tomiasi
</p>'''


class CheckboxWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.checkbox = QCheckBox(self)
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.checkbox)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

    def isChecked(self):
        return self.checkbox.isChecked()

    def setChecked(self, checked):
        self.checkbox.setChecked(checked)

    def stateChanged(self):
        return self.checkbox.stateChanged


class ActivityTableRow:
    def __init__(self, name: str, weight: float, effort: float, done: bool, grade: float = None):
        self.name = name
        self.weight = weight
        self.effort = effort
        self._done = done
        if done:
            if grade is None:
                raise ValueError(
                    "Se a atividade já foi realizada, deve-se fornecer a nota obtida")
            self.grade = grade

    def __str__(self):
        return f"ActivityTableRow({self.name}, {self.weight}, {self.effort}, {self._done}, {self.grade if self._done else None})"

    def bindToTable(self, table: QTableWidget, row: int):
        self.table = table
        self.nameItem = QTableWidgetItem(self.name)
        self.nameItem.setFlags(self.nameItem.flags() | Qt.ItemIsEditable)
        self.weightItem = QTableWidgetItem(str(self.weight))
        self.weightItem.setFlags(self.weightItem.flags() | Qt.ItemIsEditable)
        self.effortItem = QTableWidgetItem(str(self.effort))
        self.effortItem.setFlags(self.effortItem.flags() | Qt.ItemIsEditable)
        self.gradeItem = QTableWidgetItem(
            str(self.grade if self._done else ''))
        # when gradeItem is changed, update grade
        self.table.itemChanged.connect(self.updateState)

        if self._done:
            self.gradeItem.setFlags(self.gradeItem.flags() | Qt.ItemIsEditable)
        else:
            self.gradeItem.setFlags(
                self.gradeItem.flags() & ~Qt.ItemIsEditable)

        self.checkboxWidget = CheckboxWidget()
        self.checkboxWidget.setChecked(self._done)
        self.checkboxWidget.stateChanged().connect(self.updateState)
        self.table.blockSignals(True)
        table.setItem(row, 0, self.nameItem)
        table.setItem(row, 1, self.weightItem)
        table.setItem(row, 2, self.effortItem)
        table.setItem(row, 3, self.gradeItem)
        table.setCellWidget(row, 4, self.checkboxWidget)
        self.table.blockSignals(False)

    def updateState(self):
        # Bloqueando signals para evitar recursão infinita
        self.table.blockSignals(True)
        # Atualiza nome da atividade
        self.name = self.nameItem.text()
        # Atualiza valor de se a atividade foi realizada
        self._done = self.checkboxWidget.isChecked()

        weight_from_str = self.weightItem.text() if self.weightItem.text() != '' else '0.0'
        try:
            self.weight = float(weight_from_str)
            if self.weight < 0.0 or self.weight > 1.0:
                raise ValueError()
        except ValueError:
            # Generate error box
            QErrorMessage(self.table).showMessage(f'''
Peso inválido: "{weight_from_str}", deve ser um número real entre 0 e 1''')
            self.weight = 0.0
        self.weightItem.setText(str(self.weight))

        effort_from_str = self.effortItem.text() if self.effortItem.text() != '' else '0.0'
        try:
            self.effort = float(effort_from_str)
            if self.effort < 0.0:
                raise ValueError()
        except ValueError:
            # Generate error box
            QErrorMessage(self.table).showMessage(f'''
Esforço inválido: "{effort_from_str}", deve ser um número real maior que 0''')
            self.effort = 0.0
        self.effortItem.setText(str(self.effort))

        if self._done:
            grade_from_str = self.gradeItem.text() if self.gradeItem.text() != '' else '0.0'
            try:
                self.grade = float(grade_from_str)
                if self.grade < 0.0 or self.grade > 10.0:
                    raise ValueError()
            except ValueError:
                # Generate error box
                QErrorMessage(self.table).showMessage(f'''
Nota inválida: "{grade_from_str}", deve ser um número real entre 0 e 10''')
                self.grade = 0.0
            self.gradeItem.setText(str(self.grade))
            self.gradeItem.setFlags(self.gradeItem.flags() | Qt.ItemIsEditable)
        else:
            self.gradeItem.setText('')
            self.gradeItem.setFlags(
                self.gradeItem.flags() & ~Qt.ItemIsEditable)
            self.grade = None
        self.table.blockSignals(False)


class ActivitiesTable(QTableWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(
            ["Atividade", "Peso", "Esforço/Nota", "Nota", "Já realizada?"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rows = []
        self.rows.append(ActivityTableRow("Prova 1", 0.4, 2., True, 8.0))
        self.rows.append(ActivityTableRow("Trabalho 1", 0.1, 1., True, 10.0))
        self.rows.append(ActivityTableRow("Prova 2", 0.4, 3., False))
        self.rows.append(ActivityTableRow("Trabalho 2", 0.1, 1., False))
        self.setRowCount(len(self.rows))
        for i, item in enumerate(self.rows):
            item.bindToTable(self, i)

    def insertRow(self):
        self.rows.append(ActivityTableRow("Nova atividade", 0.1, 1, False))
        super().insertRow(len(self.rows)-1)
        self.rows[-1].bindToTable(self, len(self.rows)-1)

    def removeRow(self, row):
        super().removeRow(row)
        self.rows.pop(row)

    def removeSelectedRows(self):
        unique_rows = set(index.row() for index in self.selectedIndexes())
        rows_reverse_sorted = sorted(unique_rows, reverse=True)
        for row in rows_reverse_sorted:
            self.removeRow(row)


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Otimização de média")
        self.setGeometry(300, 300, 800, 600)
        self.initMenuBar()
        self.initLayout()
        self.addTableToLayout()
        self.addSpinBoxToLayout()
        self.addButtonsToLayout()

    def initLayout(self):
        self.centralWidget = QWidget()
        self.centralLayout = QVBoxLayout()
        self.centralWidget.setLayout(self.centralLayout)
        self.setCentralWidget(self.centralWidget)

    def addTableToLayout(self):
        self.table = ActivitiesTable(self)
        self.centralLayout.addWidget(self.table)

    def addSpinBoxToLayout(self):
        self.spinBox = QSpinBox()
        self.spinBox.setRange(0, 168)
        self.spinBox.setSingleStep(1)
        self.spinBox.setValue(10)
        self.spinBox.setSuffix(" horas semanais")
        self.spinBox.setWrapping(True)
        self.spinBox.setAlignment(Qt.AlignCenter)
        self.spinBoxAndButtonLayout = QHBoxLayout()
        self.spinBoxAndButtonLayout.addWidget(self.spinBox)
        self.centralLayout.addLayout(self.spinBoxAndButtonLayout)

    def addButtonsToLayout(self):
        self.addRowButton = QPushButton("Adicionar")
        self.addRowButton.clicked.connect(self.table.insertRow)
        self.removeRowButton = QPushButton("Remover")
        self.removeRowButton.clicked.connect(self.table.removeSelectedRows)
        self.debugButton = QPushButton("Debug")
        self.debugButton.clicked.connect(
            lambda: [print(row) for row in self.table.rows])
        self.calculateButton = QPushButton("Calcular")
        self.calculateButton.clicked.connect(self.calculate)
        self.spinBoxAndButtonLayout.addWidget(self.addRowButton)
        self.spinBoxAndButtonLayout.addWidget(self.removeRowButton)
        self.spinBoxAndButtonLayout.addWidget(self.debugButton)
        self.spinBoxAndButtonLayout.addWidget(self.calculateButton)

    def initMenuBar(self):
        self.menuBar = self.menuBar()
        self.aboutMenu = self.menuBar.addMenu("Sobre")
        self.aboutMenu.addAction("Sobre o programa")
        # texto pop-up quando clicando em "Sobre o programa"
        self.aboutMenu.triggered.connect(self.about)
        # Bind menuBar to window
        self.setMenuBar(self.menuBar)

    def calculate(self):
        # Solver de programação linear
        solver = pywraplp.Solver.CreateSolver("GLOP")
        if not solver:
            return
        # Verificando se a soma dos pesos é igual (ou muito próxima) a 1
        weights_sum = sum(row.weight for row in self.table.rows)
        if abs(weights_sum - 1.0) > 1e-3:
            QErrorMessage(self).showMessage(
                f'''
A soma dos pesos deve ser igual a 1, mas é {weights_sum:.3f}''')
        # Atividades não realizadas ainda
        not_done = [row for row in self.table.rows if not row._done]
        # Variáveis de decisão: esforço para cada uma das atividades não realizadas
        efforts = [solver.NumVar(0.0, solver.infinity(), row.name)
                   for row in not_done]
        # Primeira restrição: soma dos esforços não pode ser maior que o tempo disponível
        solver.Add(solver.Sum(efforts) <= self.spinBox.value())
        # Para cada esforço, a nota obtida é o esforço vezes a nota por hora
        # de forma que essa nota resultante não pode ser superior a 10.
        for row, effort in zip(not_done, efforts):
            solver.Add(effort * row.effort <= 10.0)
        # Função objetivo, maximizar a média ponderada das notas
        solver.Maximize(solver.Sum(row.weight * row.effort *
                        effort for row, effort in zip(not_done, efforts)))
        # Resolve o problema
        status = solver.Solve()
        if status == pywraplp.Solver.OPTIMAL:
            print("Solution:")
            print(f"Objective value = {solver.Objective().Value():0.1f}")
        else:
            print("The problem does not have an optimal solution.")

    def about(self):
        if (hasattr(self, "aboutWindow")):
            self.aboutWindow.show()
            return
        else:
            self.aboutWindow = QDialog(self)
            self.aboutWindow.setWindowTitle("Sobre o programa")
            self.aboutWindow.setFixedSize(400, 300)
            self.aboutWindow.setModal(True)
            self.aboutWindow.label = QLabel(ABOUT_TEXT)
            self.aboutWindow.label.setWordWrap(True)
            self.aboutWindow.label.setParent(self.aboutWindow)
            self.aboutWindow.label.move(10, 10)
            self.aboutWindow.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())
