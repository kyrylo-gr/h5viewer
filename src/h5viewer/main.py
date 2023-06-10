# pylint: disable=C0103, I1101
"""
H5viewer for labmate.

@authors:
started by: SamuelDeleglise,
after: kyrylo-gr

https://stackoverflow.com/questions/63611190/python-macos-builds-run-from-terminal-but-crash-on-finder-launch
"""
import logging
import os
from labmate.path import Path
import time
import sys
import re
import os.path as osp
from typing import List
from PyQt6 import QtWidgets
from PyQt6 import QtGui, QtCore


from labmate.syncdata import SyncData  # pylint: disable=E0401

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
STARTED_FROM_CMD = True


def get_aqm_variable(code):
    code2 = code[:code.find('.analysis_cell')]
    return code2[code2.rfind('\n')+1:]


def convert_analyse_code(code: str, filepath: str):
    aqm_variable = get_aqm_variable(code)
    code = (code
            .replace('%', '#%')
            .replace("fig.show()", "plt.show()")
            .replace(f"{aqm_variable}.analysis_cell(",
                     f'{aqm_variable}.analysis_cell(filepath="{filepath}",')
            .replace(f"{aqm_variable}.save_fig(", f"# {aqm_variable}.save_fig(")
            )
    if "plt." in code and "plt.show" not in code:
        code += "\nplt.show()\n"

    return code


def get_outline(data: str):
    outline = []
    title_pattern = "#={3,} *([^=]*) *={3,}"
    for match in re.finditer(title_pattern, data):
        outline.append(match.group(1))

    return outline


def has_outline(name: str):
    return name.endswith('.py')


# ====== Logger ======
class QTextLogger(logging.Handler):
    def __init__(self):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit()
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


def catch_and_log(function):
    def wrapper(*args, **kwargs):
        try:
            func = function(*args, **kwargs)
            return func
        except Exception as error:  # pylint: disable=W0718
            logger.exception(error)
            return None

    return wrapper


# ====== Highlighter ======
class PythonSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.highlighting_rules = []

        self.initializeFormats()

    def initializeFormats(self):
        self.classical_format = QtGui.QTextCharFormat()
        self.classical_format.setForeground(QtGui.QColor("#000000"))

        self.keyword_format = QtGui.QTextCharFormat()
        self.keyword_format.setForeground(QtGui.QColor("#cf222e"))

        self.function_format = QtGui.QTextCharFormat()
        self.function_format.setForeground(QtGui.QColor("#8250df"))

        self.var_format = QtGui.QTextCharFormat()
        self.var_format.setForeground(QtGui.QColor("#A3DAFF"))

        self.comment_format = QtGui.QTextCharFormat()
        self.comment_format.setForeground(QtGui.QColor("#6e7781"))

        self.string_format = QtGui.QTextCharFormat()
        self.string_format.setForeground(QtGui.QColor("#0a3069"))

        self.number_format = QtGui.QTextCharFormat()
        self.number_format.setForeground(QtGui.QColor("#0550ae"))

        self.equal_format = QtGui.QTextCharFormat()
        self.equal_format.setForeground(QtGui.QColor("#0550ae"))

        self.class_format = QtGui.QTextCharFormat()
        self.class_format.setForeground(QtGui.QColor("#953800"))

        keywords = "(?:True|False|None|def|class|if|else|elif|for|\
            while|in|not|and|or|with|assert|return|raise|global|import|from)"
        var = "\\w+"

        self.highlighting_rules = [
            # abc(
            (f"\\b({var})\\(", self.function_format),
            # abc. ...
            (f"\\b(({var}\\.)+)", self.class_format),
            # if ...
            (f"\\b({keywords})\\b", self.keyword_format),
            # var =
            # (f"\\b({var})(( )?=)", self.var_format),
            # if var
            # (f"\\b{keywords} {var}", self.var_format),
            # .var
            (f"\\.({var})", self.function_format),
            # def abc(var, var = ...)
            # (f"\\bdef {var}(\\((({var})[, =]*)*\\))", self.classical_format),
            # "...", '...'
            ("((\"[^\"]*\")|('[^']*'))", self.string_format),
            # 123, 123.32, 123_123
            ("\\b((\\-?[\\d_]+\\.?\\d*)(e(\\-?[\\d_]+\\.?\\d*))?)",
             self.number_format),
            # equal format
            ("(?:\\w| )(=)(?:\\w| )", self.equal_format),
            # ...
            ("(#[^\n]*)", self.comment_format),
            # long comments
            ('("""(.*\n?))?', self.string_format),
        ]

    @catch_and_log
    def highlightBlock(self, text: str) -> None:
        for pattern, format_ in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                if len(match.regs) < 2:
                    continue
                start_end = match.regs[1]
                self.setFormat(start_end[0],
                               start_end[1] - start_end[0],
                               format_)

# ====== TextCode ======


class QTextCode(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.syntax_highlighter = PythonSyntaxHighlighter(self.document())


# ====== FindField ======
class QFindField(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setPlaceholderText("Find")


class CentralWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lay = QtWidgets.QVBoxLayout()

        self.find_field = QFindField()
        self.find_field.returnPressed.connect(self.find_text)
        self.lay.addWidget(self.find_field)

        self.text_edit = QTextCode()  # QtWidgets.QTextEdit()
        self.text_edit.setAcceptDrops(False)
        self.lay.addWidget(self.text_edit)

        self.run_analysis_button = QtWidgets.QPushButton("Run analysis")
        self.run_analysis_button.setVisible(False)
        self.lay.addWidget(self.run_analysis_button)

        self.preview_button = QtWidgets.QPushButton("Show preview")
        self.preview_button.setVisible(False)
        self.lay.addWidget(self.preview_button)

        self.setLayout(self.lay)

    def find_text(self):
        text_to_find = self.find_field.text()

        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            start = cursor.selectionEnd()
        else:
            start = 0
        text = self.text_edit.toPlainText()[start:]
        pos = text.find(text_to_find)
        if pos < 0:
            if start > 0:
                cursor.clearSelection()
                self.text_edit.setTextCursor(cursor)
                return self.find_text()
            return
        cursor.setPosition(pos+start)
        cursor.select(cursor.SelectionType.WordUnderCursor)
        self.setFocus()
        self.text_edit.setFocus()
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()
        self.find_field.setFocus()


# ====== Left menu ======
class TreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent, txt):
        super().__init__(parent)
        self.setText(0, txt)


class StructureWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)

    def get_row_tree_reversed(self, index: QtCore.QModelIndex) -> List[str]:
        # print("get_row_tree", index, index.data())
        info = [index.data()]
        if index.parent().isValid():
            info.extend(self.get_row_tree_reversed(index.parent()))
        return info

    def get_row_tree(self, index) -> List[str]:
        info = list(reversed(self.get_row_tree_reversed(index)))
        # print("info", info)
        return info

    def update(self, structure: dict):
        # print("structure", structure)
        self.clear()
        self.add_to_node(self, structure)
        self.collapseAll()

    def add_to_node(self, node, structure: dict, path=None):
        if path is None:
            path = [0]
        structure = sorted(list(structure.items()))
        for i, (key, value) in enumerate(structure):
            path[-1] = i
            row = TreeWidgetItem(node, key)
            if isinstance(value, dict):
                self.add_to_node(row, value, path)


# ====== Main menu ======
class EditorWindow(QtWidgets.QMainWindow):
    data = None
    file_path = None
    last_tree_index = None

    def __init__(self, parent=None):
        super().__init__(parent)

        hlayout = QtWidgets.QHBoxLayout()
        self.structure = StructureWidget()
        self.structure.doubleClicked.connect(self.tree_double_click)

        self.logTextBox = QTextLogger()

        self.logTextBox.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s\n'))
        logging.getLogger(__name__).addHandler(self.logTextBox)
        logging.getLogger(__name__).setLevel(logging.DEBUG)

        vhlayout = QtWidgets.QVBoxLayout()
        vhlayout.addWidget(self.structure, 3)
        vhlayout.addWidget(self.logTextBox.widget, 1)
        vhwidget = QtWidgets.QWidget()
        vhwidget.setLayout(vhlayout)
        hlayout.addWidget(vhwidget, 2)

        self.central_widget = CentralWidget(self)
        self.text_edit = self.central_widget.text_edit

        self.central_widget.run_analysis_button.clicked.connect(
            self.run_analysis)
        self.central_widget.preview_button.clicked.connect(
            self.preview_mermaid)

        hlayout.addWidget(self.central_widget, 3)

        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(hlayout)
        self.setCentralWidget(main_widget)
        self.resize(800, 500)

        self.setAcceptDrops(True)

        self.last_tree_structure = ['none']

    # ====== Properties ======

    @property
    def filename(self):
        if self.file_path is None:
            raise ValueError(
                "There is no file_path specified. Should open_file first")
        return osp.split(self.file_path)[-1]

    @property
    def filedir(self):
        if self.file_path is None:
            raise ValueError(
                "There is no file_path specified. Should open_file first")
        return osp.abspath(osp.dirname(self.file_path))

    # ====== Drag and drop ======
    @catch_and_log
    def dragEnterEvent(self, event: QtGui.QDropEvent):  # pylint: disable=C0103
        if len(event.mimeData().urls()) == 1:
            event.accept()
        logger.warning("dropped, but it should be just one file")

    @catch_and_log
    def dropEvent(self, event: QtGui.QDropEvent):  # pylint: disable=C0103
        for url in event.mimeData().urls():
            logger.debug("File dropped %s", str(url))
            if url.isLocalFile():
                file = url.path()  # url.url().replace("file://", "")
                if os.name == "nt" and file[0] == '/':
                    file = file[1:]
                self.open_file(file)
            break

    @catch_and_log
    def open_file(self, file_path):
        self.file_path = file_path
        self.structure.clear()

        self.data = SyncData(file_path, open_on_init=False)
        self.structure.update(self.data.keys_tree())
        self.setWindowTitle(osp.split(file_path)[1])

    # ====== Run Analysis ======
    @catch_and_log
    def run_analysis(self, *args):
        if self.file_path is None:
            raise ValueError(
                "There is no file_path specified. Should open_file first")

        analysis_code_original = self.text_edit.toPlainText()
        init_code = ""
        init_code_file = osp.join(self.filedir, "init_analyse.py")

        source = None
        if osp.exists(init_code_file):
            with open(init_code_file, 'r', encoding='utf-8') as file:
                line = file.readline()
                while (line.startswith('#')):
                    if line.startswith('# SOURCE: '):
                        source = line[len("# SOURCE: "):-1]
                        break
                    line = file.readline()

            sys.path.append(self.filedir)
            logger.debug("Import init code")
            init_code = "from init_analyse import *\n"

        # analysis_code = convert_analyse_code(analysis_code_original, self.filename)

        code = init_code + analysis_code_original
        if source:
            with open(osp.join(self.filedir, "__code_to_run__.py"),
                      "w", encoding="utf=8") as file:
                file.write(code)
            import subprocess  # pylint: disable=C0415
            command = f"{source}&& cd {self.filedir}&& python __code_to_run__.py"
            print(command)
            ret = subprocess.run(
                command, capture_output=True, shell=True, check=False)

            logger.info("from subprocess: %s", ret.stdout.decode())
            if ret.stderr.decode():
                logger.error(ret.stderr.decode())
            os.remove(osp.join(self.filedir, "__code_to_run__.py"))

        else:
            exec(code)  # pylint: disable=W0122)

    # ====== Preview mermaid ======
    @catch_and_log
    def preview_mermaid(self, *args):
        if self.file_path is None:
            raise ValueError(
                "There is no file_path specified. Should open_file first")
        md = self.text_edit.toPlainText()
        pattern = "```mermaid((.*\n?)*)```"
        found = re.search(pattern, md)
        if found is None:
            return
        mermaid = found.group(1)
        # print(mermaid)
        path = Path('preview_mermaid.html')
        link = f"""<h1>{self.filename} {self.last_tree_structure[-1]}</h1><div class="mermaid">{mermaid}</div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{startOnLoad:true}});</script>"""
        with open(path, 'w', encoding="utf-8") as file:
            file.write(link)

        import webbrowser  # pylint: disable=C0415, E0401
        webbrowser.open(f"file://{path.absolute()}")
        time.sleep(1)
        os.remove(path.absolute())

    # ====== Tree interaction ======
    @catch_and_log
    def close_last_open_tree_item(self):
        if self.last_tree_index is None:
            return
        last_item = self.structure.itemFromIndex(self.last_tree_index)
        if has_outline(last_item.text(0)):
            self.structure.collapse(self.last_tree_index)

    @catch_and_log
    def tree_double_click(self,
                          index: QtCore.QModelIndex) -> None:
        assert self.data, "Data should be loaded before reading"
        return self.structure_selected(index)

    @catch_and_log
    def structure_selected(self,
                           index: QtCore.QModelIndex):

        tree_to_item = self.structure.get_row_tree(index)
        item = self.structure.itemFromIndex(index)

        self.central_widget.run_analysis_button.setVisible(False)
        self.central_widget.preview_button.setVisible(False)

        data = self.data.get_dict(tree_to_item[0])
        for key in tree_to_item[1:]:
            if isinstance(data, dict):
                # print(key, data)
                data = data.get(key)
            else:
                cursor = self.text_edit.textCursor()
                text = self.text_edit.toPlainText()
                pattern = f"# *={{3,}} *({key}) *={{3,}}"
                found = re.search(pattern, text)
                if found is None:
                    return
                cursor.setPosition(found.start())
                self.central_widget.setFocus()
                self.text_edit.setFocus()
                self.text_edit.setTextCursor(cursor)
                self.text_edit.ensureCursorVisible()
                return

        self.close_last_open_tree_item()
        self.last_tree_index = index
        self.last_tree_structure = tree_to_item

        if isinstance(data, dict):
            if item.childCount() == 0:
                for key in sorted(list(data.keys())):
                    TreeWidgetItem(item, key)
            self.text_edit.setText(
                ("It contains more data" if len(data) > 0 else str(data)))
        else:
            if tree_to_item[0].startswith("analysis_cell"):
                self.central_widget.run_analysis_button.setVisible(True)
                data = convert_analyse_code(str(data), self.filename)
            if isinstance(data, str) and "```mermaid" in data:
                self.central_widget.preview_button.setVisible(True)

            if has_outline(tree_to_item[-1]):
                if item.childCount() == 0:
                    for key in get_outline(data):
                        TreeWidgetItem(item, key)

            self.text_edit.setPlainText(str(data))  # .setText(str(data))

        return None

    # ====== Shortcuts ======
    def keyPressEvent(self, event):
        if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier and event.key() == QtCore.Qt.Key.Key_F:
            if not self.central_widget.find_field.isVisible():
                self.central_widget.find_field.setVisible(True)
                self.central_widget.find_field.setFocus()
            else:
                self.central_widget.find_field.setVisible(False)
        else:
            super().keyPressEvent(event)


def main():
    APP = QtWidgets.QApplication(sys.argv)
    APP.setStyle("fusion")
    style_sheet = """
        QWidget {
            background-color: #FFFFFF;
            color: #000000;
        }

    """

    APP.setStyleSheet(style_sheet)

    if os.name == 'nt':
        try:
            from ctypes import windll
            myappid = 'mycompany.myproduct.subproduct.version'
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            basedir = osp.dirname(__file__)
            APP.setWindowIcon(QtGui.QIcon(osp.join(basedir, 'favicon.ico')))
        except ImportError:
            pass

    EDITOR = EditorWindow(None)
    EDITOR.show()

    if len(sys.argv) > 1:
        FILE_PATH = sys.argv[1]
        logger.info("Opening file %s", FILE_PATH)
        EDITOR.open_file(FILE_PATH)
    APP.exec()


if __name__ == "__main__":
    main()
