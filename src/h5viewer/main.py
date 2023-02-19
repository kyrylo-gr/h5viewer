# -*- coding: utf-8 -*-
"""
@author: Samuel Deleglise

All questions to the author.

https://stackoverflow.com/questions/63611190/python-macos-builds-run-from-terminal-but-crash-on-finder-launch
"""
import logging
import os
import sys
import os.path as osp
import traceback
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
            .replace(f"{aqm_variable}.analysis_cell(", f'{aqm_variable}.analysis_cell(filepath="{filepath}",')
            .replace(f"{aqm_variable}.save_fig(", f"# {aqm_variable}.save_fig(")
            )
    if "plt." in code and "plt.show" not in code:
        code += "\nplt.show()\n"

    return code


class QTextLogger(logging.Handler):
    def __init__(self):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit()
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class CentralWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lay = QtWidgets.QVBoxLayout()
        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setAcceptDrops(False)

        self.lay.addWidget(self.text_edit)
        self.run_analysis_button = QtWidgets.QPushButton("Run analysis")
        self.lay.addWidget(self.run_analysis_button)
        self.setLayout(self.lay)


class TreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent, txt):
        super().__init__(parent)
        self.setText(0, txt)


class StructureWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)

    def get_row_tree_reversed(self, index: QtCore.QModelIndex) -> List[str]:
        info = [index.data()]
        if index.parent().isValid():
            info.extend(self.get_row_tree(index.parent()))
        return info

    def get_row_tree(self, index) -> List[str]:
        return list(reversed(self.get_row_tree_reversed(index)))

    def update(self, structure: dict):
        print("structure", structure)
        self.clear()
        self.add_to_node(self, structure)
        self.collapseAll()

    def add_to_node(self, node, structure: dict, path=None):
        if path is None:
            path = [0]
        for i, (key, value) in enumerate(structure.items()):
            path[-1] = i
            row = TreeWidgetItem(node, key)
            if isinstance(value, dict):
                self.add_to_node(row, value, path)


def catch_and_log(function):
    def wrapper(*args, **kwargs):
        try:
            func = function(*args, **kwargs)
            return func
        except Exception as error:
            logger.exception(error)
            return None

    return wrapper


class EditorWindow(QtWidgets.QMainWindow):
    data = None
    file_path = None

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
        self.run_analysis_button = self.central_widget.run_analysis_button
        self.run_analysis_button.clicked.connect(self.run_analysis)
        hlayout.addWidget(self.central_widget, 3)

        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(hlayout)
        self.setCentralWidget(main_widget)
        self.resize(800, 500)

        self.setAcceptDrops(True)

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
    def run_analysis(self, *args):
        if self.file_path is None:
            raise ValueError(
                "There is no file_path specified. Should open_file first")

        analysis_code_original = self.text_edit.toPlainText()
        init_code = ""
        init_code_file = osp.join(self.file_dir, "init_analyse.py")

        source = None
        if osp.exists(init_code_file):
            with open(init_code_file, 'r', encoding='utf-8') as file:
                line = file.readline()
                while(line.startswith('#')):
                    if line.startswith('# SOURCE: '):
                        source = line[len("# SOURCE: "):-1]
                        break
                    line = file.readline()

            sys.path.append(self.file_dir)
            logger.debug("Import init code")
            init_code = "from init_analyse import *\n"

        # analysis_code = convert_analyse_code(analysis_code_original, self.filename)

        try:
            code = init_code + analysis_code_original
            if source:
                with open(osp.join(self.file_dir, "__code_to_run__.py"),
                          "w", encoding="utf=8") as file:
                    file.write(code)
                import subprocess
                command = f"{source}&& cd {self.file_dir}&& python __code_to_run__.py"
                print(command)
                ret = subprocess.run(
                    command, capture_output=True, shell=True, check=False)

                logger.info("from subprocess: %s", ret.stdout.decode())
                if ret.stderr.decode():
                    logger.error(ret.stderr.decode())
                os.remove(osp.join(self.file_dir, "__code_to_run__.py"))

            else:
                exec(code,)  # pylint: disable=W0122)

        except Exception:
            print(traceback.format_exc())

    @property
    def filename(self):
        if self.file_path is None:
            raise ValueError(
                "There is no file_path specified. Should open_file first")
        return osp.split(self.file_path)[-1]

    @property
    def file_dir(self):
        if self.file_path is None:
            raise ValueError(
                "There is no file_path specified. Should open_file first")
        return osp.abspath(osp.dirname(self.file_path))

    @catch_and_log
    def tree_double_click(self, index: QtCore.QModelIndex) -> None:
        assert self.data, "Data should be loaded before reading"
        tree_to_item = self.structure.get_row_tree(index)
        item = self.structure.itemFromIndex(index)
        return self.structure_selected(item, tree_to_item)

    @catch_and_log
    def structure_selected(self, item, tree_to_item):
        item_is_analysis_cell = tree_to_item[0].startswith("analysis_cell")
        self.run_analysis_button.setVisible(item_is_analysis_cell)

        data = self.data
        for key in tree_to_item:
            data = data[key]
        if isinstance(data, dict):
            if item.childCount() == 0:
                for keys in data.keys():
                    TreeWidgetItem(item, keys)
            self.text_edit.setText(
                ("It contains more data" if len(data) > 0 else str(data)))
        else:
            if item_is_analysis_cell:
                data = convert_analyse_code(str(data), self.filename)
            self.text_edit.setText(str(data))

        return None

    @catch_and_log
    def open_file(self, file_path):
        self.file_path = file_path
        self.structure.clear()

        self.data = SyncData(file_path, open_on_init=False)
        self.structure.update(self.data.keys_tree())
        self.setWindowTitle(osp.split(file_path)[1])


def main():
    APP = QtWidgets.QApplication(sys.argv)
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
