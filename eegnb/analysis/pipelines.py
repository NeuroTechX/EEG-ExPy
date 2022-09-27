"""

CLI Pipeline for Analysis of EEGNB Recorded Data

To do: 
1. Beautify analysis pdf
2. Handle cli automated errors for report creation
3. Implement interface to erp plot function for cli

Usage:

For Recorded Data:

from eegnb.analysis.pipelines import create_analysis_report()
create_analysis_report(experiment, eegdevice, subject, session, filepath)s

For Example Datasets:

from eegnb.analysis.pipelines import example_analysis_report()
example_analysis_report()

"""

# Some standard pythonic imports
import os
from collections import OrderedDict
import warnings
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
from typing import Dict

warnings.filterwarnings('ignore')

# MNE functions
from mne import Epochs,find_events, create_info
from mne.io import RawArray

# EEG-Notebooks functions
from eegnb import generate_save_fn
from eegnb.analysis.utils import load_data,plot_conditions, load_csv_as_raw, fix_musemissinglines
from eegnb.analysis.analysis_report import get_html
from eegnb.datasets import fetch_dataset
from eegnb.devices.utils import EEG_INDICES, SAMPLE_FREQS
from pathlib import Path

DATA_DIR = os.path.join(os.path.expanduser("~/"), ".eegnb", "data")
eegdevice, experiment_name, subject_id, session_nb, example_flag = None, None, None, None, False

def load_eeg_data(experiment, subject=1, session=1, device_name='muse2016_bfn', tmin=-0.1, tmax=0.6, baseline=None, 
                    reject={'eeg': 5e-5}, preload=True, verbose=1,
                        picks=[0,1,2,3], event_id = OrderedDict(House=1,Face=2), fnames=None, example=False):
    """
    Loads EEG data from the specified experiment, subject, session, and device.
    Returns the raw and epochs objects.

    Procedure
    1. Loads the data using file names and retrives if not already present
    2. Epochs the data
    3. Computes the ERP
    4. Returns the raw and ERP objects

    Parameters
    ----------
    experiment : Experiment Name
    subject : Subject ID of performed experiment
    session : Session ID of performed experiment
    device_name : Device used for performed experiment
    tmin : Start time of the epochs in seconds, relative to the time-locked event.
    tmax : End time of the epochs in seconds, relative to the time-locked event.
    baseline : Not very sure..?
    reject : Rejection parameters for the epochs.
    preload : If True, preload the epochs into memory.
    verbose : If True, print out messages.
    picks : Channels to include in the analysis.
    event_id : Dictionary of event_id's for the epochs
    fnames : File names of the experiment data, if not passed, example files are used
    """

    # If not using the example dataset, load the data from the specified experiment using load_csv_as_raw
    if not example:

        # Obataining the specific parameters to load the data into MNE object
        sfreq = SAMPLE_FREQS[device_name]
        ch_ind = EEG_INDICES[device_name]

        # Generate file names if not passed
        if fnames is None:
            raw = load_data(subject_id=subject, session_nb=session, experiment=experiment, device_name=device_name, site="local", data_dir=os.path.join(os.path.expanduser('~/'),'.eegnb', 'data'))

        else:
            # Replace Ch names has arbitarily been set to None
            if device_name in ["muse2016", "muse2", "museS"]:   
                raw = load_csv_as_raw([fnames], sfreq=sfreq, ch_ind=ch_ind, aux_ind=[5], replace_ch_names=None, verbose=verbose)
            else:
                raw = load_csv_as_raw([fnames], sfreq=sfreq, ch_ind=ch_ind, replace_ch_names=None, verbose=verbose)

            # Getting the subject and session
            subject, session = fnames.split('_')[1], fnames.split('_')[2]

    # If using the example dataset, load the data from the example dataset
    else:
        subject, session = 1, 1

        # Loading Data
        eegnb_data_path = os.path.join(os.path.expanduser('~/'),'.eegnb', 'data')
        experiment_data_path = os.path.join(eegnb_data_path, experiment, 'eegnb_examples')

        # If dataset hasn't been downloaded yet, download it
        if not os.path.isdir(experiment_data_path):
            fetch_dataset(data_dir=eegnb_data_path, experiment=experiment, site='eegnb_examples')

        raw = load_data(1,1,
                        experiment=experiment, site='eegnb_examples', device_name=device_name,
                        data_dir = eegnb_data_path)

    # Visualising the power spectrum 
    raw.plot_psd(show=False)
    
    # Filtering the data under a certain frequency range
    raw.filter(1,30, method='iir')

    # Visualising the power spectrum
    fig = raw.plot_psd(fmin=1, fmax=30, show=False)

    # Saving the figure so it can be accessed by the pdf creation. Automatically deleted when added to the pdf.
    plt.tight_layout()
    plt.savefig("power_spectrum.png")
    plt.show(block=False)
    plt.pause(10)
    plt.close()

    # Epoching
    # Create an array containing the timestamps and type of each stimulus (i.e. face or house)
    events = find_events(raw)

    # Create an MNE Epochs object representing all the epochs around stimulus presentation
    epochs = Epochs(raw, events=events, event_id=event_id,
                    tmin=tmin, tmax=tmax, baseline=baseline,
                    reject=reject, preload=preload,
                    verbose=verbose, picks=picks)

    print('sample drop %: ', (1 - len(epochs.events)/len(events)) * 100)
    print(epochs)

    experimental_parameters = {"eeg_device": device_name, "experiment_name": experiment, "subject_id": subject, "session_nb": session, "example_flag": example, "drop_percent": (1 - len(epochs.events)/len(events)) * 100}

    return epochs, experimental_parameters


def make_erp_plot(epochs, experimental_parameters:Dict, conditions=OrderedDict(House=[1],Face=[2]), ci=97.5, n_boot=1000, title='',
                   diff_waveform=None, #(1, 2))
                   channel_order=[1,0,2,3]):
    """
    Plots the ERP for the specified conditions.

    Parameters
    ----------
    epochs : MNE Epochs object
    conditions : OrderedDict holding the conditions to plot
    ci: confidence interval
    n_boot: number of bootstrap samples
    title: title of the plot
    diff_waveform: tuple of two integers indicating the channels to compare
    channel_order: list of integers indicating the order of the channels to plot
    """

    fig, ax = plot_conditions(epochs, conditions=conditions,
                            ci=97.5, n_boot=1000, title='',
                            diff_waveform=None, #(1, 2))
                            channel_order=[1,0,2,3]) # reordering of epochs.ch_names according to [[0,2],[1,3]] of subplot axes

    # Autoscaling the y axis to a tight fit to the ERP
    for i in [0,1,2,3]: ax[i].autoscale(tight=True)

    # for a in ax.ravel (): a.autoscale(tight=True) 

    # Saving the figure so it can be accessed by the pdf creation. Automatically deleted when added to the pdf.
    
    # Makes sure that the axis labels are not cut out
    plt.tight_layout()
    plt.savefig("erp_plot.png")
    plt.show(block=False)
    plt.pause(10)
    plt.close()

    # Creating the pdf, needs to be discussed whether we want to call it here or seperately.
    create_pdf(experimental_parameters)

def create_pdf(experimental_parameters:Dict):
    """Creates analysis report using the power spectrum and ERP plots that are saved in the directory"""

    # Unpack the experimental parameters
    eegdevice, experiment, subject, session, example, drop_percentage = experimental_parameters.values()

    # Getting the directory where the report should be saved
    save_dir = get_save_directory(experiment=experiment, eegdevice=eegdevice, subject=subject, session=session, example=example, label="analysis")
    
    #get whole filepath
    filepath = os.path.join(save_dir, 'analysis_report_{}.html'.format(datetime.now().strftime("%d-%m-%Y_%H-%M-%S")))
    
    # Get the report 
    report_html = get_html(experimental_parameters)

    # Save html file
    with open(filepath, 'w') as f:
        f.write(report_html)
    
    # Informing the user that the report has been saved
    print('Analysis report saved to {}\n'.format(filepath))
    print("Open as pdf by clicking the following link: {}{}".format("file:///", filepath))

def get_save_directory(experiment, eegdevice, subject, session, example, label):
    """ Returns save directory as a String for the analysis report """
    
    if not example:
        site='local'
    else:
        site='eegnb_examples'

    # Getting the directory where the analysis report should be saved
    save_path = os.path.join(os.path.expanduser("~/"),'.eegnb', label)
    save_path = os.path.join(save_path, experiment, site, eegdevice, "subject{}".format(subject), "session{}".format(session))

    # Creating the directory if it doesn't exist
    if not os.path.isdir(save_path):
        os.makedirs(save_path)
    
    return save_path

def create_analysis_report_(experiment, eegdevice, subject=None, session=None, data_path=None, bluemuse_file_fix=False):
    """ Interface with the erp plot function, basically cli type instructions """

    # Prompt user to enter options and then take inputs and do the necessary
    epochs, experimental_parameters = load_eeg_data(experiment=experiment, subject=subject, session=session, device_name=eegdevice, example=False, fnames=data_path)
    make_erp_plot(epochs, experimental_parameters)

def example_analysis_report():
    """ Example of how to use the analysis report function """
    experiment = ["visual-N170", "visual-P300"]
    experiment_choice = experiment[int(input("Choose an experiment: {} 0 or 1".format(experiment)))]

    if experiment_choice == "visual-N170":
        epochs, experimental_parameters = load_eeg_data(experiment_choice, example=True)
        make_erp_plot(epochs, experimental_parameters)
    else:
        epochs, experimental_parameters = load_eeg_data('visual-P300', device_name='muse2016', event_id={'Non-Target': 1, 'Target': 2}, example=True)
        make_erp_plot(epochs, experimental_parameters, conditions=OrderedDict(NonTarget=[1],Target=[2]))