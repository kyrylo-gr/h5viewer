from PyQt6.QtCore import Qt, QRegularExpression, QRegularExpressionMatchIterator, QRegularExpressionMatch
from PyQt6.QtGui import QTextCharFormat, QColor, QFont, QSyntaxHighlighter
from PyQt6.QtWidgets import QApplication, QTextEdit


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.highlighting_rules = []
        self.keyword_format = QTextCharFormat()
        self.comment_format = QTextCharFormat()
        self.string_format = QTextCharFormat()
        self.number_format = QTextCharFormat()

        self.initializeFormats()

    def initializeFormats(self):
        self.keyword_format.setForeground(QColor("#0000FF"))
        self.keyword_format.setFontWeight(QFont.Weight.Bold)

        self.comment_format.setForeground(QColor("#008000"))

        self.string_format.setForeground(QColor("#A020F0"))

        self.number_format.setForeground(QColor("#FF0000"))

        self.highlighting_rules = [
            ("\\b(True|False|None|def|class|if|else|elif|for|while|in|not|and|or|with)",
             self.keyword_format),
            ("\"[^\"]*\"", self.string_format),
            ("'[^']*'", self.string_format),
            ("\\b\\d+\\.?\\d*", self.number_format),
            ("#[^\n]*", self.comment_format),
        ]

    # def highlightBlock(self, text: str) -> None:
    #     print("text", text)
    #     for pattern, format_ in self.highlighting_rules:
    #         expression = QRegularExpression(pattern)
    #         matches: QRegularExpressionMatchIterator = expression.globalMatch(
    #             text)

    #         while matches.hasNext():
    #             match: QRegularExpressionMatch = matches.next()
    #             print("match", match)
    #             self.setFormat(match.capturedStart(),
    #                            match.capturedLength(), format_)

    def highlightBlock(self, text: str) -> None:
        print("text", text)
        for pattern, format_ in self.highlighting_rules:
            # print("pattern", pattern)
            # matches: QRegularExpressionMatchIterator = pattern.globalMatch(
            #     text)
            import re
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(),
                               match.end() - match.start(), format_)
            # while matches.hasNext():
                # match: QRegularExpressionMatch = matches.next()

            # for match in matches.swap(matches):
            #     # match: QRegularExpressionMatch = matches.next()
                print("match", match)
                # self.setFormat(match.capturedStart(),
                #    match.capturedLength(), format_)


app = QApplication([])

code = """
def greet(name):
    print(f"Hello, {name}!")  # Comment
    greeting = "Hi, " + name  # String
    number = 42  # Number
    if number > 10:  # Keyword
        print(greeting)

greet("World")
"""

editor = QTextEdit()
highlighter = PythonSyntaxHighlighter(editor.document())

editor.setPlainText(code)
editor.show()

app.exec()
