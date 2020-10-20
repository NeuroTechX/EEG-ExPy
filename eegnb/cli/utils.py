
from eegnb.experiments.visual_n170 import n170
from eegnb.experiments.visual_p300 import p300
from eegnb.experiments.visual_ssvep import ssvep
from eegnb.experiments.auditory_oddball import auditoryaMMN

import h5py
import numpy as np, pandas as pd

def run_experiment(experiment, record_duration, eeg_device, save_fn):


    if experiment == 'visual-N170':
        n170.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)
    elif experiment == 'visual-P300':
        p300.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)
    elif experiment == 'visual-SSVEP':
        ssvep.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)
    elif experiment == 'auditory_oddball':
        conditions_file = 'MUSE_conditions.mat'
        F = h5py.File(conditions_file, 'r')#['museEEG']
        highPE = np.squeeze(F['museEEG']['design']['highPE'][:]).astype(int)
        lowPE = np.squeeze(F['museEEG']['design']['lowPE'][:]).astype(int)
        inputs = np.squeeze(F['museEEG']['design']['inputs'][:]).astype(int)
        oddball = np.squeeze(F['museEEG']['design']['oddball'][:]).astype(int)
        oddball-=1 
        stim_types = oddball
        itis = np.ones_like(oddball)*0.5
        newAdditionalMarkers = [];
        for i in range(0, len(highPE)):
            newAdditionalMarker = str(stim_types[i]) + str(highPE[i]) + str(lowPE[i])
            newAdditionalMarkers.append(newAdditionalMarker)
        additional_labels = {'labels' : newAdditionalMarkers}
        auditoryaMMN.present(record_duration=record_duration,stim_types=stim_types,itis=itis, additional_labels = {'labels' : newAdditionalMarkers}, eeg=eeg_device, save_fn=save_fn)

