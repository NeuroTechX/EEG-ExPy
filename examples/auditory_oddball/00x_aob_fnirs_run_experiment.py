"""
Auditory Oddball run experiment, plus kernel
=============================================

This example demonstrates the initiation of an EEG and fNIRS stream with eeg-notebooks, and how to run 
an experiment. 

"""

###################################################################################################  
# Setup
# ---------------------  
#  
# Imports
import os,numpy as np
from eegnb import generate_save_fn
from eegnb.devices.eeg import EEG
from eegnb.devices.fnirs import FNIRS
#from eegnb.experiments.visual_n170 import n170
from eegnb.experiments.auditory_oddball import aMMN 
import h5py

# Define some variables
eeg_device_name = 'museS_bfb'
fnirs_device_name = "kernelflow"
experiment = "aMMN" #  i#"visual_n170"
subject_id = 0
session_nb = 0
record_duration = 20


#conditions_file = 'MUSE_conditions.mat' 
conditions_file = '../../eegnb/experiments/auditory_oddball/MUSE_conditions.mat' # JG_MOD
F = h5py.File(conditions_file, 'r')#['museEEG']
highPE = np.squeeze(F['museEEG']['design']['highPE'][:]).astype(int)
lowPE = np.squeeze(F['museEEG']['design']['lowPE'][:]).astype(int)
inputs = np.squeeze(F['museEEG']['design']['inputs'][:]).astype(int)
oddball = np.squeeze(F['museEEG']['design']['oddball'][:]).astype(int)
oddball-=1 
stim_types = oddball
itis = np.ones_like(oddball)*0.5 
###################################################################################################
# Initiate EEG device
# ---------------------
#
# Start EEG device

eeg_device = None
#eeg_device = EEG(device=eeg_device_name, serial_port='/dev/ttyACM0')#board_name)


fnirs_device = FNIRS(device=fnirs_device_name)

## Create save file name
eeg_save_fn = generate_save_fn(eeg_device_name, experiment, subject_id, session_nb)
#print(eeg_save_fn)

###################################################################################################  
# Run experiment
# ---------------------  
#  
aMMN.present(eeg = eeg_device, fnirs = fnirs_device, stim_types=stim_types,
              itis=itis, duration=record_duration,save_fn=eeg_save_fn)

