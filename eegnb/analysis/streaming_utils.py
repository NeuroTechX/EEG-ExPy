import copy
from copy import deepcopy
import math
import logging
import sys
from collections import OrderedDict
from glob import glob
from typing import Union, List
from time import sleep, time
from pynput import keyboard
import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from mne import create_info, concatenate_raws
from mne.io import RawArray
from mne.channels import make_standard_montage
from mne.filter import create_filter
from matplotlib import pyplot as plt
from scipy import stats
from scipy.signal import lfilter, lfilter_zi

from eegnb import _get_recording_dir
from eegnb.devices.eeg import EEG
#from eegnb.devices.utils import EEG_INDICES, SAMPLE_FREQS
from eegnb.analysis.utils import thres_stds

# this should probably not be done here
sns.set_context("talk")
sns.set_style("white")


logger = logging.getLogger(__name__)



# Bjareholt Tools
# ==================
# From    https://github.com/ErikBjare/thesis/blob/master/src/eegclassify/clean.py
# ------


def channel_filter(
    X: np.ndarray,
    n_chans: int,
    sfreq: int,
    device_backend: str,
    device_name: str,
    low: float = 3,
    high: float = 40,
    verbose: bool = False,
) -> np.ndarray:
    """Inspired by viewer_v2.py in muse-lsl"""
    if device_backend == "muselsl":
        pass
    elif device_backend == "brainflow":
        if 'muse' not in device_name: # hacky; muse brainflow devices do in fact seem to be in correct units
            X = X / 1000 # adjust scale of readings
    else:
        raise ValueError(f"Unknown backend {device_backend}")
    
    window = 10
    n_samples = int(sfreq * window)
    data_f = np.zeros((n_samples, n_chans))

    af = [1.0]
    bf = create_filter(data_f.T, sfreq, low, high, method="fir", verbose=verbose)

    zi = lfilter_zi(bf, af)
    filt_state = np.tile(zi, (n_chans, 1)).transpose()
    filt_samples, filt_state = lfilter(bf, af, X, axis=0, zi=filt_state)

    return filt_samples





def check(eeg: EEG, n_samples=256) -> pd.Series:
    """
    Usage:
    ------

    from eegnb.devices.eeg import EEG
    from eegnb.analysis.utils import check
    eeg = EEG(device='museS')
    check(eeg, n_samples=256)

    """

    df = eeg.get_recent(n_samples=n_samples)
    
    # seems to be necessary to give brainflow cnxn time to settle
    if len(df) != n_samples: 
      sleep(10) 
      df = eeg.get_recent(n_samples=n_samples) 

    assert len(df) == n_samples

    n_channels = eeg.n_channels
    sfreq = eeg.sfreq
    device_backend = eeg.backend
    device_name = eeg.device_name

    vals = df.values[:, :n_channels]
    df.values[:, :n_channels] = channel_filter(vals, 
                                    n_channels,
                                    sfreq,
                                    device_backend,
                                    device_name)

    std_series = df.std(axis=0)
    
    return std_series



def check_report(eeg: EEG, n_times: int=60, pause_time=5, thres_std_low=None, thres_std_high=None, n_goods=2,n_inarow=5):
    """
    Usage:
    ------
    from eegnb.devices.eeg import EEG
    from eegnb.analysis.utils import check_report
    eeg = EEG(device='museS')
    check_report(eeg)

    The thres_std_low & thres_std_high values are the 
    lower and  upper bound of accepted
    standard deviation for a quality recording.

    thresholds = {
        bad: 15,
        good: 10,
        great: 1.5 // Below 1 usually indicates not connected to anything
    }
    """

    # If no upper and lower std thresholds set in function call,
    # set thresholds based on the following per-device name defaults
    edn = eeg.device_name
    flag = False
    if thres_std_low is None:
        if edn in thres_stds.keys():
            thres_std_low = thres_stds[edn][0]
    if thres_std_high is None:
        if edn in thres_stds.keys():
            thres_std_high = thres_stds[edn][1]
            
    print("\n\nRunning signal quality check...")
    print(f"Accepting threshold stdev between: {thres_std_low} - {thres_std_high}")

    CHECKMARK = "√"
    CROSS = "x"
        
    print(f"running check (up to) {n_times} times, with {pause_time}-second windows")
    print(f"will stop after {n_goods} good check results in a row")

    good_count=0

    n_samples = int(pause_time*eeg.sfreq)

    sleep(5)

    for loop_index in range(n_times):
        print(f'\n\n\n{loop_index+1}/{n_times}')
        std_series = check(eeg, n_samples=n_samples)

        indicators = "\n".join(
        [
            f"  {k:>4}: {CHECKMARK if v >= thres_std_low and v <= thres_std_high else CROSS}  (std: {round(v, 1):>5})"
                for k, v in std_series.iteritems()
        ]
                              )
        print("\nSignal quality:")
        print(indicators)

        bad_channels = [k for k, v in std_series.iteritems() if v < thres_std_low or v > thres_std_high ]
        if bad_channels:
            print(f"Bad channels: {', '.join(bad_channels)}")
            good_count=0  # reset good checks count if there are any bad chans
        else:
            print('No bad channels')
            good_count+=1

        if good_count==n_goods:
            print("\n\n\nAll good! You can proceed on to data collection :) ")
            break

        # after every n_inarow trials ask user if they want to cancel or continue
        if (loop_index+1) % n_inarow == 0:
            print(f"\n\nLooks like you still have {len(bad_channels)} bad channels after {loop_index+1} tries\n")

            prompt_time = time()
            print(f"Starting next cycle in 5 seconds, press C and enter to cancel")
            c_key_pressed = False

            def update_key_press(key):
                if key.char == 'c':
                    globals().update(c_key_pressed=True)
            listener = keyboard.Listener(on_press=update_key_press)
            listener.start()
            while time() < prompt_time + 5:
                if c_key_pressed:
                    print("\nStopping signal quality checks!")
                    flag = True
                    break
            listener.stop()
        if flag: 
            break  


