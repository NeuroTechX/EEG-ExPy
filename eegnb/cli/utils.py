
from eegnb.experiments.visual_n170 import n170
from eegnb.experiments.visual_p300 import p300
from eegnb.experiments.visual_ssvep import ssvep
from eegnb.experiments.auditory_oddball import auditoryaMMN
from eegnb.experiments.auditory_ssaep import ssaepupdate

import os

import h5py
import numpy as np, pandas as pd

def makeoddball(inputs, rep):
    #based on inputs, creating oddball paradigms markers depending on "switch"
    value = inputs[0]
    count = 0
    markerArray = []
    for i in range(len(inputs)):
        if inputs[i] == value:
            count += 1
            if count == rep:
                markerArray.append(1)
            else:
                markerArray.append(3)
        else:
            if count == rep + 1:
                markerArray.append(2)
            
            else:
                markerArray.append(4)
            value = inputs[i]
            count = 1
    return markerArray

def maketonesnums(num):
    newArray = []
    for i in range(num):
        newArray.append(90000+i)
    return newArray   
      

def run_experiment(experiment, record_duration, eeg_device, save_fn):
    if experiment == 'visual-N170':
        n170.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)
    elif experiment == 'visual-P300':
        p300.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)
    elif experiment == 'visual-SSVEP':
        ssvep.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)
    elif experiment == 'auditory-SSAEP':
        ssaepupdate.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)
    elif experiment == 'auditory_oddball':
        conditions_file = os.path.join(os.path.dirname(os.path.abspath("__file__")), "MUSE_conditions.mat")
        F = h5py.File(conditions_file, 'r')#['museEEG']
        highPE = np.squeeze(F['museEEG']['design']['highPE'][:]).astype(int)
        lowPE = np.squeeze(F['museEEG']['design']['lowPE'][:]).astype(int)
        inputs = np.squeeze(F['museEEG']['design']['inputs'][:]).astype(int)

        #based on inputs, creating oddball paradigms markers depending on "switch"
        tonenums = maketonesnums(1800)
        oddball3 = makeoddball(inputs, 3)
        oddball4 = makeoddball(inputs, 4)
        oddball5 = makeoddball(inputs, 5)
        oddball6 = makeoddball(inputs, 6)

        #modifying 0s in PE definitions of tones that represent markers to 3s to avoid loss of trials instead of ignoring them
        for i in range(len(highPE)):
            if highPE[i] == 0:
                highPE[i] = 3
            if lowPE[i] == 0:
                lowPE[i] = 3  
           
        #1 is standard/bottom, 2 is deviant/high, 3 is "baseline trial"

        stim_types = inputs
        itis = np.ones_like(inputs)*0.5 

        newAdditionalMarkers = [];

        for i in range(0, len(highPE)):
            newAdditionalMarker = str(oddball3[i]) + str(oddball4[i]) + str(oddball5[i]) + str(oddball6[i]) + str(highPE[i]) + str(lowPE[i])
            newAdditionalMarkers.append(newAdditionalMarker)

        additional_labels = {'labels' : newAdditionalMarkers}
        auditoryaMMN.present(record_duration=record_duration,stim_types=stim_types,itis=itis, additional_labels = {'labels' : newAdditionalMarkers}, eeg=eeg_device, save_fn=save_fn)
        

