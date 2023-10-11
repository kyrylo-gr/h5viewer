import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTextEdit, QPushButton, QWidget
from PyQt6.QtCore import Qt
import difflib


class TextDiffViewer(QMainWindow):
    def __init__(self, original_text, modified_text):
        super().__init__()

        self.setWindowTitle("Text Diff Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.original_text = original_text
        self.modified_text = modified_text

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.layout.addWidget(self.text_edit)

        self.show_diff_button = QPushButton("Show Differences", self)
        self.show_diff_button.clicked.connect(self.show_differences)
        self.layout.addWidget(self.show_diff_button)

    def show_differences(self):
        d = difflib.Differ()
        diff = list(d.compare(self.original_text.splitlines(),
                    self.modified_text.splitlines()))

        diff_result = []
        for line in diff:
            if line.startswith('- '):
                diff_result.append(
                    f'<span style="background-color: #FFCCCC;">{line[2:]}</span>')
            elif line.startswith('+ '):
                diff_result.append(
                    f'<span style="background-color: #C2FFC2;">{line[2:]}</span>')
            else:
                diff_result.append(line[2:])

        formatted_html = '<br>'.join(diff_result)
        self.text_edit.setHtml(formatted_html)


original_text = """
for i in range(10):
    print(1)
    a = 2

a = 15
b = 123_000
c = dasd
a=123
#b=3123

d= 1.3e7
r=2e9
w=e2
ww=2e2e2

"""
modified_text = """
for i in range(10):
    print(1)
    a = 2

a = 10
b = 123_000
c = dasd
a=123
#b=3123

d= 1.3e7
r=2e9
w=e2
ww=2e2e2

"""


def main():
    app = QApplication(sys.argv)
    window = TextDiffViewer(original_text, modified_text)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
