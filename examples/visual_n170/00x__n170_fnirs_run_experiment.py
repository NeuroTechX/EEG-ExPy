"""
N170 run experiment
===============================

This example demonstrates the initiation of an EEG stream with eeg-notebooks, and how to run 
an experiment. 

"""

###################################################################################################  
# Setup
# ---------------------  
#  
# Imports
import os
from eegnb import generate_save_fn
from eegnb.devices.eeg import EEG
from eegnb.devices.fnirs import FNIRS
from eegnb.experiments.visual_n170 import n170

# Define some variables
#board_name = "muse2_bfn"
eeg_device_name = "museS_bfb"
experiment = "visual_n170"
subject_id = 1
session_nb = 1
record_duration = 20 # 300 # 20 # 120

fnirs_device_name = 'kernelflow'

###################################################################################################
# Initiate EEG device
# ---------------------
#

# Start EEG device

#eeg_device = None
eeg_device = EEG(device=eeg_device_name, serial_port='/dev/ttyACM0')#board_name)

fnirs_device = FNIRS(device=fnirs_device_name)

## Create save file name
eeg_save_fn = generate_save_fn(eeg_device_name, experiment, subject_id, session_nb)
#print(eeg_save_fn)


###################################################################################################  
# Run experiment
# ---------------------  
#  

#n170.present(duration=record_duration, eeg=eeg_device, fnirs= fnirs_device,save_fn=save_fn)
n170.present(eeg = eeg_device, fnirs = fnirs_device, duration=record_duration,
             save_fn=eeg_save_fn)

