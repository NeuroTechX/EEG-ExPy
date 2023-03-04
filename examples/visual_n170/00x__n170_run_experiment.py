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
from eegnb.devices.eeg import EEG
from eegnb.experiments import VisualN170

# Define some variables

# Experiment type
experiment = VisualN170()

# EEG device
experiment.eeg = EEG(device="cyton")  # "muse")

# Test subject id
subject_id = 0

# Session number
session_nb = 0

# Experiment recording duration
experiment.duration = 120

###################################################################################################  
# Run experiment
# ---------------------  
#
experiment.run()

# Saved csv location
print(experiment.save_fn)
