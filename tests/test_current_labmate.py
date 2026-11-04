"""Read current Labmate files without running their saved analysis code."""

import ast
import hashlib
import importlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from dh5 import DH5
from dh5.errors import ReadOnlyKeyError
from labmate.acquisition.acquisition_data import NotebookAcquisitionData
from labmate.acquisition.analysis_data import AnalysisData
from PyQt6 import QtCore, QtWidgets


class CurrentLabmateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.settings_directory = tempfile.TemporaryDirectory()
        with patch.object(QtCore.QStandardPaths, "writableLocation",
                          return_value=cls.settings_directory.name):
            cls.viewer = importlib.import_module("h5viewer.main")

    @classmethod
    def tearDownClass(cls):
        cls.viewer.SETTINGS.sync()
        cls.settings_directory.cleanup()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.window = self.viewer.EditorWindow()
        self.addCleanup(self.close_window)

    def close_window(self):
        self.window.close()
        self.viewer.logger.removeHandler(self.window.logTextBox)
        self.application.processEvents()

    def make_acquisition(self, name, gain=2):
        path = self.directory / name
        acquisition = NotebookAcquisitionData(
            str(path), cell="t = [0, 1, 2]\ny = [0, 1, 0]", save_files=False
        )
        acquisition.update(t=np.array([0., 1., 2.]), y=np.array([0., gain, 0.]),
                           calibration={"gain": gain}).save()
        AnalysisData(str(path), cell="aqm.analysis_cell(filepath='old.h5')\nresult = aqm.data.y * 2")
        return path

    def test_current_labmate_data_and_saved_analysis_can_be_browsed_read_only(self):
        path = self.make_acquisition("measurement.h5")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        self.window.open_file(str(path))
        self.assertEqual(self.window.file_path, str(path.resolve()))
        self.assertIsInstance(self.window.data, DH5)
        np.testing.assert_equal(self.window.get_data_by_key(keys=["t"]), [0., 1., 2.])
        self.assertEqual(self.window.get_data_by_key(keys=["calibration", "gain"]), 2)
        self.assertIn("analysis_cells", self.window.data.keys())
        root = next(self.window.structure.topLevelItem(index)
                    for index in range(self.window.structure.topLevelItemCount())
                    if self.window.structure.topLevelItem(index).text(0) == "analysis_cells")
        self.window.structure_selected(self.window.structure.indexFromItem(root))
        self.assertGreater(root.childCount(), 0)
        self.window.structure_selected(self.window.structure.indexFromItem(root.child(0)))
        converted = self.window.text_edit.toPlainText()
        call = next(node for node in ast.walk(ast.parse(converted))
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "analysis_cell")
        self.assertEqual(ast.literal_eval(call.keywords[0].value), str(path.resolve()))
        with self.assertRaises(ReadOnlyKeyError):
            self.window.data["y"] = [9, 9, 9]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_opening_a_second_file_preserves_previous_file_comparison(self):
        first = self.make_acquisition("first.h5", gain=2)
        second = self.make_acquisition("second.h5", gain=3)
        self.window.open_file(str(first))
        self.window.open_file(str(second))
        self.assertEqual(self.window.file_path, str(second.resolve()))
        self.assertIsInstance(self.window.previous_data, DH5)
        self.assertEqual(self.window.get_data_by_key(self.window.previous_data,
                                                   ["calibration", "gain"]), 2)
        self.window.last_tree_structure = ["calibration", "gain"]
        self.window.show_difference(None)
        self.assertIn("2", self.window.text_edit.toPlainText())
        self.assertIn("3", self.window.text_edit.toPlainText())

    def test_missing_file_is_not_created_and_existing_view_is_kept(self):
        path = self.make_acquisition("existing.h5")
        self.window.open_file(str(path))
        missing = self.directory / "missing.h5"
        with self.assertLogs(self.viewer.logger, level="ERROR"):
            self.window.open_file(str(missing))
        self.assertFalse(missing.exists())
        self.assertEqual(self.window.file_path, str(path.resolve()))

    def test_analysis_conversion_replaces_saved_file_arguments_and_escapes_paths(self):
        code = ("# an analysis cell\n"
                "aqm.analysis_cell(\n"
                "    filename='old.h5', filepath='another.h5', experiment_id=123,\n"
                "    download_timeout=10, cell=source, prerun=prepare)\n"
                "result = y % 3\nlabel = 'signal (%)'\n")
        path = "C:\\Data\\L'été\\measurement.h5"
        converted = self.viewer.convert_analyse_code(code, path)
        calls = [node for node in ast.walk(ast.parse(converted))
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                 and node.func.attr == "analysis_cell"]
        self.assertEqual(len(calls), 1)
        self.assertEqual([keyword.arg for keyword in calls[0].keywords],
                         ["filepath", "cell", "prerun"])
        self.assertEqual(ast.literal_eval(calls[0].keywords[0].value), path)
        self.assertIn("result = y % 3", converted)
        self.assertIn("signal (%)", converted)

    def test_analysis_conversion_handles_positional_filenames_and_notebook_magic(self):
        code = "%matplotlib inline\naqm.analysis_cell('old.h5', cell=source)\n"
        converted = self.viewer.convert_analyse_code(code, "/data/current.h5")
        tree = ast.parse(converted)
        call = tree.body[0].value
        self.assertEqual(call.args, [])
        self.assertEqual(ast.literal_eval(call.keywords[0].value), "/data/current.h5")
        self.assertTrue(converted.startswith("#%matplotlib inline"))


if __name__ == "__main__":
    unittest.main()
