"""
SSVEP run experiment
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
from eegnb.experiments.visual_ssvep import ssvep

# Define some variables
board_name = 'muse'
experiment = 'visual_ssvep'
subject = 'test'
record_duration=120

###################################################################################################
# Initiate EEG device
# ---------------------
#
# Start EEG device
eeg_device = EEG(device=board_name)

# Create save file name
save_fn = generate_save_fn(board_name, experiment, subject)
print(save_fn)

###################################################################################################  
# Run experiment
# ---------------------  
#  
ssvep.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)
