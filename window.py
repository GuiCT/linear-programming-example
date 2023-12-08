
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog, QLabel, QVBoxLayout, QTableWidget, QHeaderView, QWidget, QTableWidgetItem, QSpinBox, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox

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

    def bindToTable(self, table: QTableWidget, row: int):
        self.table = table
        self.nameItem = QTableWidgetItem(self.name)
        self.nameItem.setFlags(self.nameItem.flags() & ~Qt.ItemIsEditable)
        self.weightItem = QTableWidgetItem(str(self.weight))
        self.weightItem.setFlags(self.weightItem.flags() & ~Qt.ItemIsEditable)
        self.effortItem = QTableWidgetItem(str(self.effort))
        self.effortItem.setFlags(self.effortItem.flags() & ~Qt.ItemIsEditable)
        self.gradeItem = QTableWidgetItem(
            str(self.grade if self._done else ''))

        if self._done:
            self.gradeItem.setFlags(self.gradeItem.flags() | Qt.ItemIsEditable)
        else:
            self.gradeItem.setFlags(
                self.gradeItem.flags() & ~Qt.ItemIsEditable)

        self.checkboxWidget = CheckboxWidget()
        self.checkboxWidget.setChecked(self._done)
        self.checkboxWidget.stateChanged().connect(self.updateState)
        table.setItem(row, 0, self.nameItem)
        table.setItem(row, 1, self.weightItem)
        table.setItem(row, 2, self.effortItem)
        table.setItem(row, 3, self.gradeItem)
        table.setCellWidget(row, 4, self.checkboxWidget)

    def updateState(self):
        self._done = self.checkboxWidget.isChecked()
        if self._done:
            self.grade = 0.0
            self.gradeItem.setText(str(self.grade))
            self.gradeItem.setFlags(self.gradeItem.flags() | Qt.ItemIsEditable)
        else:
            self.gradeItem.setText('')
            self.gradeItem.setFlags(
                self.gradeItem.flags() & ~Qt.ItemIsEditable)
            self.grade = None


class ActivitiesTable(QTableWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(
            ["Atividade", "Peso", "Esforço/Nota", "Nota", "Já realizada?"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rows = []
        self.rows.append(ActivityTableRow("Prova 1", 0.4, 2, True, 8.0))
        self.rows.append(ActivityTableRow("Trabalho 1", 0.1, 1, True, 10.0))
        self.rows.append(ActivityTableRow("Prova 2", 0.4, 3, False))
        self.rows.append(ActivityTableRow("Trabalho 2", 0.1, 1, False))
        self.setRowCount(len(self.rows))
        for i, item in enumerate(self.rows):
            item.bindToTable(self, i)


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
        self.addRowButton = QPushButton("Adicionar atividade")
        self.calculateButton = QPushButton("Calcular")
        self.spinBoxAndButtonLayout.addWidget(self.addRowButton)
        self.spinBoxAndButtonLayout.addWidget(self.calculateButton)

    def initMenuBar(self):
        self.menuBar = self.menuBar()
        self.aboutMenu = self.menuBar.addMenu("Sobre")
        self.aboutMenu.addAction("Sobre o programa")
        # texto pop-up quando clicando em "Sobre o programa"
        self.aboutMenu.triggered.connect(self.about)
        # Bind menuBar to window
        self.setMenuBar(self.menuBar)

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
