"""
P100 Load and Visualize Data
===============================

This example demonstrates loading, organizing, and visualizing EP response data from the visual P100 experiment. 

An animation of a checkerboard reversal is shown(the checkerboard squares' colours are toggled once each half a second).

The data used is the first subject and first session of the one of the eeg-notebooks P100 example datasets.
It was recorded using an OpenBCI Ultracortex EEG headset(Mark IV) with it's last five electrodes placed in the headset's
node locations of (PO1, Oz, PO2, P3 and P4).
These headset node locations were used to fit around a Meta Quest 2 headset, which tilted/angled the headset backwards
so that the real locations of the electrodes are closer to the occipital lobe - O1, Iz, O2, PO1 and PO2.
The session consisted of using the Meta Quest 2 linked with a PC to display the checkerboard reversal animation
for thirty seconds of continuous recording.  

We first use the `fetch_datasets` to obtain a list of filenames. If these files are not already present 
in the specified data directory, they will be quickly downloaded from the cloud. 

After loading the data from the occiptal channels, we place it in an MNE `Epochs` object, and then an `Evoked` object to obtain
the trial-averaged delay of the response. 

The final figure plotted at the end shows the P100 response EP waveform. 

"""

###################################################################################################
# Setup
# ---------------------

# Some standard pythonic imports
import os
import warnings
warnings.filterwarnings('ignore')

# MNE functions
from mne import Epochs,find_events,Evoked

# EEG-Notebooks functions
from eegnb.analysis.utils import load_data,plot_conditions
from eegnb.datasets import fetch_dataset

###################################################################################################
# Load Data
# ---------------------
#
# We will use the eeg-notebooks P100 example dataset
#
# Note that if you are running this locally, the following cell will download
# the example dataset, if you do not already have it.
#

###################################################################################################

eegnb_data_path = os.path.join(os.path.expanduser('~/'),'.eegnb', 'data')    
experiment = 'visual_p100'
p100_data_path = os.path.join(eegnb_data_path, experiment, 'eegnb_examples')

# If dataset hasn't been downloaded yet, download it 
# if not os.path.isdir(p100_data_path):
#     fetch_dataset(data_dir=eegnb_data_path, experiment=experiment, site='eegnb_examples')

subject = 0
session = 0
raw = load_data(subject,session,
                experiment=experiment, site='local', device_name='cyton',
                data_dir = eegnb_data_path)

###################################################################################################
# Visualize the power spectrum
# ----------------------------

raw.plot_psd()

###################################################################################################
# Filtering
# ----------------------------

raw.filter(1,30, method='iir')
raw.plot_psd(fmin=1, fmax=30);


###################################################################################################
# Epoching
# ----------------------------

# Create an array containing the timestamps and type of each stimulus (i.e. first or second checkerboard)
events = find_events(raw)
event_id = {'First checkerboard': 1, 'Second checkerboard': 2}

# Create an MNE Epochs object representing all the epochs around stimulus presentation
epochs = Epochs(raw, events=events, event_id=event_id, 
                tmin=-0.1, tmax=0.4, baseline=None,
                reject={'eeg': 100e-6}, preload=True, 
                verbose=False, picks=[3,4,5,6,7])
print('sample drop %: ', (1 - len(epochs.events)/len(events)) * 100)
epochs

###################################################################################################
# Epoch average
# ----------------------------
evoked = epochs.average()
plot = evoked.plot(spatial_colors=True)


###################################################################################################
# VEP P100 is llocated approx between 100 and 150ms.
# ----------------------------

channel, latency, value = evoked.get_peak(tmin=0.1, tmax=0.15, mode='pos', return_amplitude=True)
latency = int(round(latency * 1e3))  # convert to milliseconds
value = int(round(value * 1e6))      # convert to µV
print('Peak of {} µV at {} ms in channel {}'.format(value, latency, channel))