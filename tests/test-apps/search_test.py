import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtGui import QTextCursor, QColor, QTextDocument
from PyQt6.QtCore import Qt, QRegularExpression


class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()

        self.search_label = QLabel("Find:")
        self.search_edit = QLineEdit()
        self.search_edit.returnPressed.connect(self.find_next)

        self.find_button = QPushButton("Find Next")
        self.find_button.clicked.connect(self.find_next)

        layout.addWidget(self.search_label)
        layout.addWidget(self.search_edit)
        layout.addWidget(self.find_button)

        self.setLayout(layout)

    def find_next(self):
        search_term = self.search_edit.text()
        if search_term:
            text_edit = self.parent().text_edit
            found = text_edit.find(search_term)
            if found:
                self.parent().highlight_found_text()
            else:
                text_edit.moveCursor(QTextCursor.MoveOperation.Start)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Search Example")

        self.text_edit = QTextEdit()
        self.setCentralWidget(self.text_edit)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_F:
            dialog = SearchDialog(self)
            dialog.show()
        else:
            super().keyPressEvent(event)

    def highlight_found_text(self):
        search_term = self.sender().parent().search_edit.text()
        text_cursor = self.text_edit.textCursor()
        format = QTextDocument.FindFlag(0)
        format |= QTextDocument.FindFlag(0).FindWholeWords
        format |= QTextDocument.FindFlag(0).FindCaseSensitively

        while text_cursor.hasSelection():
            text_cursor.clearSelection()

        found_cursor = self.text_edit.document().find(
            QRegularExpression(search_term), text_cursor, format)
        if found_cursor is not None:
            self.text_edit.setTextCursor(found_cursor)
            self.text_edit.ensureCursorVisible()

            highlight_format = QTextCursor().charFormat()
            highlight_format.setBackground(QColor(255, 255, 0))
            self.text_edit.setTextCursor(found_cursor)
            self.text_edit.mergeCurrentCharFormat(highlight_format)
            self.text_edit.setTextCursor(text_cursor)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(400, 300)
    window.show()
    sys.exit(app.exec())
    
    
aqm = QApplication()

aqm.acquisition_cell("ramsey_g_e")

n_avg = 10_000

t_min, t_max, dt = 16, 50_000//4, 250//4
times_ramsey_ge = np.arange(t_min, t_max + dt//2, dt)*4

element = 'g_e'
prepare_state = 'g'

track_flux = cfg.stabilize_flux

with program() as ramsey_ge:
    n = qfunc.declare_qm_var(int)
    t = declare(int)
    meas_angle = declare(fixed)

    with for_(n, 0, n < n_avg, n + 1):
        with for_(t, t_min, t < t_max + dt//2, t + dt):  # Notice it's + da/2 to include a_max (This is only for fixed!)
            with for_each_(meas_angle, [0, 0.25]):