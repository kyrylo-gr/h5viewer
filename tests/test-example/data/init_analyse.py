# SOURCE: source /Users/4cd87a/opt/anaconda3/bin/activate phd_mask
import sys
import os
import matplotlib.pylab as plt
import matplotlib
from labmate.acquisition_notebook import AcquisitionAnalysisManager

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(os.path.join(os.path.abspath(SCRIPT_DIR), 'analyse'))
meas_dir = os.path.split(SCRIPT_DIR)[0]

aqm = AcquisitionAnalysisManager(meas_dir)

print('init_analysis')
from first import *