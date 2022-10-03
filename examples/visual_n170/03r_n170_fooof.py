"""
N170 FOOOF Analysis
===============================

This example execute a Frequency Over One Over F (FOOOF) analysis  
on the N170 faces/houses dataset, and compares it with respect to a classical
power spectra analysis. 

The data used is exactly the same as in the N170 `load_and_visualize` example. 

"""

###################################################################################################
# Setup
# ---------------------

# Some standard pythonic imports
import os

# EEG-Notebooks functions
from eegnb.analysis.utils import load_data, plot_conditions
from eegnb.datasets import fetch_dataset

# MNE functions
from mne import Epochs, find_events
from mne.time_frequency import psd_welch

# FOOOF functions
from fooof import FOOOF
from fooof.plts import plot_spectra

# Matplotlib for visualization
import matplotlib.pyplot as plt

###################################################################################################
# Load Data
# ---------------------
#
# ( See the n170 `load_and_visualize` example for further description of this)
#

eegnb_data_path = os.path.join(os.path.expanduser("~/"), ".eegnb", "data")
n170_data_path = os.path.join(eegnb_data_path, "visual-N170", "eegnb_examples")

# If dataset hasn't been downloaded yet, download it
if not os.path.isdir(n170_data_path):
    fetch_dataset(
        data_dir=eegnb_data_path, experiment="visual-N170", site="eegnb_examples"
    )

subject = 1
session = 1
raw = load_data(
    subject,
    session,
    experiment="visual-N170",
    site="eegnb_examples",
    device_name="muse2016_bfn",
    data_dir=eegnb_data_path,
)

###################################################################################################
# Filtering
# ----------------------------

raw.filter(1, 30, method="iir")
raw.plot_psd(fmin=1, fmax=30)

###################################################################################################
# Epoching
# ----------------------------

# Create an array containing the timestamps and type of each stimulus (i.e. face or house)
events = find_events(raw)
event_id = {"House": 1, "Face": 2}

# Create an MNE Epochs object representing all the epochs around stimulus presentation
epochs = Epochs(
    raw,
    events=events,
    event_id=event_id,
    tmin=-0.1,
    tmax=0.6,
    baseline=None,
    reject={"eeg": 5e-5},
    preload=True,
    verbose=False,
    picks=[0, 1, 2, 3],
)
print("sample drop %: ", (1 - len(epochs.events) / len(events)) * 100)
epochs

###################################################################################################

# Averaging epochs by event type (House, Face)
av_epochs = epochs.average(picks=[0, 1, 2, 3], by_event_type=True)

fms = list()
labels = ["House", "Face"]

# Computing PSD for each event type and evaluating FOOOF
for i, e in enumerate(av_epochs):
    power, freq = psd_welch(
        e,
        n_fft=len(e.times),
        n_overlap=len(e.times) / 2,
        proj=False,
        average="mean",
        window="hamming",
    )

    # A full exponential equation to fit the aperiodic component is chosen, thus an aperiodic "knee" mode is requested
    fms.append(FOOOF(aperiodic_mode="knee", verbose=False))
    fms[i].fit(freq, power[3], freq_range=[1, 30])

    # Plotting the results of FOOOF fitting spectra in the range 1-30 Hz
    fig, ax = plt.subplots(figsize=[15, 5])
    fms[i].plot(plot_peaks="line-shade", ax=ax)
    plt.title(f"FOOOF - {labels[i]}")
    plt.show(block=False)

###################################################################################################
# Results Visualization
# ----------------------------
#
# Interestingly, it is easily possible to see in the Peak Fit subplot how "Face" subgroup presents actual lower power with
# respect to "Face" one althought in the Original Spectra it could be assessed the opposite. This can be justified by the
# higher aperiodic contribute of Face subgroup that does not reflect however the oscillation activity power.
#
#

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, sharex=True, figsize=[15, 10])
plot_spectra(
    fms[0].freqs, [fms[0].power_spectrum, fms[1].power_spectrum], ax=ax1, labels=labels
)
ax1.set_title("Original Spectra")

plot_spectra(
    fms[0].freqs, [fms[0]._spectrum_flat, fms[1]._spectrum_flat], ax=ax2, labels=labels
)
ax2.set_title("Flat Spectrum (NO AP)")

plot_spectra(fms[0].freqs, [fms[0]._peak_fit, fms[1]._peak_fit], ax=ax3, labels=labels)
ax3.set_title("Peak Fit")

plot_spectra(fms[0].freqs, [fms[0]._ap_fit, fms[1]._ap_fit], ax=ax4, labels=labels)
ax4.set_title("AP Fit")
plt.show()
