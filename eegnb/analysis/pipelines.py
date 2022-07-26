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
from eegnb.analysis.utils import load_csv_as_raw,plot_conditions
from eegnb.datasets import fetch_dataset

"""

# Usage:

from pipelines import compute_erp,make_erp_plot
import glob
from collections import OrderedDict

fnames = glob.glob('C:/Users/eeg_lab/.eegnb/data/visual-N170/eegnb_examples/muse2016/subject0001/session001/*.csv')

'
epoch_kwargs = dict(tmin=-0.1, tmax=0.6, baseline=None,
                    reject={'eeg': 5e-5}, preload=True, 
                    verbose=False, picks=[0,1,2,3],
                    event_id = OrderedDict(House=1,Face=2) )

raw,erp = compute_erp(fnames,epoch_kwargs)

plot_kwargs = dict(conditions = epoch_kwargs['event_id'],
                   ci=97.5, n_boot=1000, title='',
                   diff_waveform=None, #(1, 2))
                   channel_order=[1,0,2,3]))

make_erp_plot(epochs,plot_kwargs)

"""


# Manually adjust the ylims
def compute_erp(raw, fnames,epoch_kwargs,plot_kwargs=None,do_plot=False,verbose=True,sfreq=256,
                ch_ind=[1,2,3,4]):

    # Load data
    # ----------------------------
    #raw = load_csv_as_raw(fnames,sfreq=sfreq,ch_ind=ch_ind)


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

    return epochs


def make_erp_plot(epochs,plot_kwargs):

    fig, ax = plot_conditions(epochs, **plot_kwargs)

    # Manually adjust the ylims
    for i in [0,2]: ax[i].set_ylim([-0.5,0.5])
    for i in [1,3]: ax[i].set_ylim([-1.5,2.5])


    # Make Plots
    # -----------------------------
    raw.plot_psd(fmin=1, fmax=30)
    plt.show()



import glob
from collections import OrderedDict


# Loading Data

from eegnb.analysis.utils import load_data,plot_conditions
from eegnb.datasets import fetch_dataset
import matplotlib.pyplot as plt

eegnb_data_path = os.path.join(os.path.expanduser('~/'),'.eegnb', 'data')
n170_data_path = os.path.join(eegnb_data_path, 'visual-N170', 'eegnb_examples')

# If dataset hasn't been downloaded yet, download it
if not os.path.isdir(n170_data_path):
    fetch_dataset(data_dir=eegnb_data_path, experiment='visual-N170', site='eegnb_examples');

subject = 1
session = 1
raw = load_data(subject,session,
                experiment='visual-N170', site='eegnb_examples', device_name='muse2016_bfn',
                data_dir = eegnb_data_path)


# Visualising the power spectrum 
raw.plot_psd()
plt.show()


fnames = glob.glob('C:/Users/eeg_lab/.eegnb/data/visual-N170/eegnb_examples/muse2016/subject0001/session001/*.csv')
epoch_kwargs = dict(tmin=-0.1, tmax=0.6, baseline=None,
                    reject={'eeg': 5e-5}, preload=True, 
                    verbose=False, picks=[0,1,2,3],
                    event_id = OrderedDict(House=1,Face=2))

epochs = compute_erp(raw, fnames,epoch_kwargs)

plot_kwargs = dict(conditions = epoch_kwargs['event_id'],
                ci=97.5, n_boot=1000, title='',
                diff_waveform=None, #(1, 2))
                channel_order=[1,0,2,3])

make_erp_plot(epochs,plot_kwargs)



