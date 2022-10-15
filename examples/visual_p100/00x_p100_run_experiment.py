"""
P100 run experiment
===============================

This example demonstrates the initiation of an EEG stream with eeg-notebooks, and how to run 
an experiment. 

"""

###################################################################################################  
# Setup
# ---------------------  
#  
# Imports
from eegnb import generate_save_fn
from eegnb.devices.eeg import EEG
from eegnb.experiments.visual_p100 import p100

# Define some variables
board_name = "cyton"
#Move the last five channels to positions close to the occipital lobe.
rename_channels = {'C4':'PO1', 'P7':'PO2', 'P8':'O1', 'O1':'O2', 'O2':'Iz'}
experiment = "visual_p100_both_eyes"
subject_id = 0
session_nb = 0
record_duration = 30

# Specific serial port to use e.g. something like "\\\\.\\COM3" on Windows or 
# "/dev/cu.usbserial-DM03H289" on macOS.
# Use None to prompt the user.
custom_serial_port=None

# Use a rift compatible vr headset(via windows) instead of a standard display monitor.
use_vr=False

###################################################################################################
# Initiate EEG device
# ---------------------
#
# Start EEG device

eeg_device = EEG(device=board_name, serial_port=custom_serial_port, replace_ch_names=rename_channels)

# Create save file name
save_fn = generate_save_fn(board_name, experiment, subject_id, session_nb)
print(save_fn)

###################################################################################################  
# Run experiment
# ---------------------  
#  

p100.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn, use_rift=use_vr)
