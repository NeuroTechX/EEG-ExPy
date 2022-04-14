"""
Analysis Pipelines
"""


###################################################################################################
# Setup
# ---------------------

# Some standard pythonic imports
import os
from collections import OrderedDict
import warnings
warnings.filterwarnings('ignore')

# MNE functions
from mne import Epochs,find_events

# EEG-Notebooks functions
from eegnb.analysis.utils import load_data,plot_conditions
from eegnb.datasets import fetch_dataset





"""
epoch_kwargs = dict(tmin=-0.1, tmax=0.6, baseline=None,
                    reject={'eeg': 5e-5}, preload=True, 
                    verbose=False, picks=[0,1,2,3],
                    event_id = OrderedDict(House=1,Face=2) )
"""

""""
plot_kwargs = dict(conditions = epoch_kwargs['event_id'],
                   ci=97.5, n_boot=1000, title='',
                   diff_waveform=None, #(1, 2))
                   channel_order=[1,0,2,3]))
"""



# Manually adjust the ylims
def compute_erp(fnames,epoch_kwargs,plot_kwargs=None,do_plot=False,verbose=True):


    # Load data
    # ----------------------------
    raw = load_csv_as_raw(fnames)


    # Filtering and cleaning
    # ----------------------------
    raw.filter(1,30, method='iir')


    # Epoching
    # ----------------------------

    # Create an array containing the timestamps and type of each stimulus (i.e. face or house)
    events = find_events(raw)

    # Create an MNE Epochs object representing all the epochs around stimulus presentation
    epochs = Epochs(raw, events=events, **epoch_kwargs)

    if verbose:
        print('sample drop %: ', (1 - len(epochs.events)/len(events)) * 100)




    # Epoch average
    # ----------------------------

    if do_plot:

        fig, ax = plot_conditions(epochs, **plot_kwargs)

        # Manually adjust the ylims
        #for i in [0,2]: ax[i].set_ylim([-0.5,0.5])
        #for i in [1,3]: ax[i].set_ylim([-1.5,2.5])


        # Make Plots
        # -----------------------------
        #raw.plot_psd(fmin=1, fmax=30);




