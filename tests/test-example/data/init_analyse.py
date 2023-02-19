# pylint: disable=wrong-import-order, wrong-import-position, unused-import, import-error
# flake8: noqa
# type: ignore
# SOURCE: source ~/opt/anaconda3/bin/activate test
import sys
import os
import matplotlib.pylab as plt

from labmate.acquisition_notebook import AcquisitionAnalysisManager

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(os.path.join(os.path.abspath(SCRIPT_DIR), 'analyse'))

meas_dir = os.path.split(os.path.split(SCRIPT_DIR)[0])[0]
aqm = AcquisitionAnalysisManager(meas_dir)

import main_analyse
print('init_analysis')