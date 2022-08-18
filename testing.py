

import matplotlib.pyplot as plt
import numpy as np
from eegnb.analysis.pipelines import load_eeg_data, make_erp_plot
from eegnb.analysis.utils import fix_musemissinglines

file_path = r"C:\Users\Parv\.eegnb\data\visual-N170\local\muse2\subject0001\session004\recording_2022-08-15-19.09.37.csv"

raw, epochs = load_eeg_data(experiment='visual-N170', subject=1, session=3, device_name='muse2', example=False)
make_erp_plot(epochs)
