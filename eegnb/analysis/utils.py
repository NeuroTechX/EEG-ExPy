import copy
from copy import deepcopy
import math
import logging
from collections import OrderedDict
from glob import glob
from typing import Union, List, Dict
from time import sleep, time
from numpy.core.fromnumeric import std

import pandas as pd
import numpy as np
import seaborn as sns
from mne import create_info, concatenate_raws
from mne.io import RawArray
from mne.channels import make_standard_montage
from mne.filter import create_filter
from matplotlib import pyplot as plt
from scipy.signal import lfilter, lfilter_zi

from eegnb import _get_recording_dir
from eegnb.devices.eeg import EEG
from eegnb.devices.utils import EEG_INDICES, SAMPLE_FREQS

                        

# this should probably not be done here
sns.set_context("talk")
sns.set_style("white")


logger = logging.getLogger(__name__)


def load_csv_as_raw(
    fnames: List[str],
    sfreq: float,
    ch_ind,
    aux_ind=None,
    replace_ch_names=None,
    verbose=1,
) -> RawArray:
    """Load CSV files into an MNE Raw object.

    Args:
        fnames (array_like): list of filename(s) to load. Should end with
            ".csv".
        sfreq (float): sampling frequency of the data.
        ch_ind (array_like): column indices to keep from the CSV files.

    Keyword Args:
        aux_ind (array_like or None): list of indices for columns containing
            auxiliary channels.
        replace_ch_names (array_like or None): list of channel name mappings
            for the selected columns.
        verbose (int): verbose level.

    Returns:
        (mne.io.RawArray): concatenation of the specified filenames into a
            single Raw object.
    """
    ch_ind = copy.deepcopy(ch_ind)
    n_eeg = len(ch_ind)
    if aux_ind is not None:
        n_aux = len(aux_ind)
        ch_ind += aux_ind
    else:
        n_aux = 0

    raw = []
    for fn in fnames:
        # Read the file
        data = pd.read_csv(fn)

        # Channel names and types
        ch_names = [list(data.columns)[i] for i in ch_ind] + ["stim"]
        print(ch_names)
        ch_types = ["eeg"] * n_eeg + ["misc"] * n_aux + ["stim"]

        if replace_ch_names is not None:
            ch_names = [
                c if c not in replace_ch_names.keys() else replace_ch_names[c]
                for c in ch_names
            ]
        print(ch_names)

        # Transpose EEG data and convert from uV to Volts
        data = data.values[:, ch_ind + [-1]].T
        data[:-1] *= 1e-6

        # create MNE object
        info = create_info(ch_names=ch_names, ch_types=ch_types, sfreq=sfreq, verbose=1)
        raw.append(RawArray(data=data, info=info, verbose=verbose))

    raws = concatenate_raws(raw, verbose=verbose)
    montage = make_standard_montage("standard_1005")
    raws.set_montage(montage)

    return raws


def load_data(
    subject_id: Union[str, int],
    session_nb: Union[str, int],
    device_name: str,
    experiment: str,
    replace_ch_names=None,
    verbose=1,
    site="local",
    data_dir=None,
    inc_chans=None,
) -> RawArray:
    """Load CSV files from the /data directory into a Raw object.

    This is a utility function that simplifies access to eeg-notebooks
    recordings by wrapping `load_csv_as_raw()`.
    The provided information is used to recover an eeg-notebooks recording file
    path with the following structure:

    data_dir/experiment/site/device_name/subject_str/session_str/<recording_date_time>.csv'

    where <recording_date_time> is the automatically generated file name(s)
    given at the time of recording.

    Args:
        subject_id (int or str): subject number. If 'all', load all
            subjects.
        session_nb (int or str): session number. If 'all', load all
            sessions.
        device_name (str): name of device. For a list of supported devices, see
            eegnb.analysis.utils.SAMPLE_FREQS.
        experiment (int or str): experiment name or number.
        inc_chans (array_like): (Optional) Selective list of the number of the
            channels to be imported

    Keyword Args:
        replace_ch_names (dict or None): dictionary containing a mapping to
            rename channels. Useful when e.g., an external electrode was used.
        verbose (int): verbose level.
        site (str): site of recording. If 'all', data from all sites will be
            used.
        data_dir (str or None): directory inside /data that contains the
            CSV files to load, e.g., 'auditory/'.

    Returns:
        (mne.io.RawArray): loaded EEG
    """

    subject_str = "*" if subject_id == "all" else f"subject{subject_id:04}"
    session_str = "*" if session_nb == "all" else f"session{session_nb:03}"
    if site == "all":
        site = "*"

    data_path = (
        _get_recording_dir(device_name, experiment, subject_str, session_str, site, data_dir)
        / "*.csv"
    )
    fnames = glob(str(data_path))

    sfreq = SAMPLE_FREQS[device_name]

    ch_ind = EEG_INDICES[device_name]

    if inc_chans is not None:
        ch_ind = inc_chans

    if device_name in ["muse2016", "muse2", "museS"]:
        return load_csv_as_raw(
            fnames,
            sfreq=sfreq,
            ch_ind=ch_ind,
            aux_ind=[5],
            replace_ch_names=replace_ch_names,
            verbose=verbose,
        )
    else:
        return load_csv_as_raw(
            fnames,
            sfreq=sfreq,
            ch_ind=ch_ind,
            replace_ch_names=replace_ch_names,
            verbose=verbose,
        )


def plot_conditions(
    epochs,
    conditions=OrderedDict(),
    ci=97.5,
    n_boot=1000,
    title="",
    palette=None,
    ylim=(-6, 6),
    diff_waveform=(1, 2),
    channel_count=4,
):
    """Plot ERP conditions.
    Args:
        epochs (mne.epochs): EEG epochs
    Keyword Args:
        conditions (OrderedDict): dictionary that contains the names of the
            conditions to plot as keys, and the list of corresponding marker
            numbers as value. E.g.,
                conditions = {'Non-target': [0, 1],
                               'Target': [2, 3, 4]}
        ci (float): confidence interval in range [0, 100]
        n_boot (int): number of bootstrap samples
        title (str): title of the figure
        palette (list): color palette to use for conditions
        ylim (tuple): (ymin, ymax)
        diff_waveform (tuple or None): tuple of ints indicating which
            conditions to subtract for producing the difference waveform.
            If None, do not plot a difference waveform
        channel_count (int): number of channels to plot. Default set to 4
            for backward compatibility with Muse implementations
    Returns:
        (matplotlib.figure.Figure): figure object
        (list of matplotlib.axes._subplots.AxesSubplot): list of axes
    """
    if isinstance(conditions, dict):
        conditions = OrderedDict(conditions)

    if palette is None:
        palette = sns.color_palette("hls", len(conditions) + 1)

    X = epochs.get_data() * 1e6
    times = epochs.times
    y = pd.Series(epochs.events[:, -1])

    midaxis = math.ceil(channel_count / 2)
    fig, axes = plt.subplots(2, midaxis, figsize=[12, 6], sharex=True, sharey=True)

    # get individual plot axis
    plot_axes = []
    for axis_y in range(midaxis):
        for axis_x in range(2):
            plot_axes.append(axes[axis_x, axis_y])
    axes = plot_axes

    for ch in range(channel_count):
        for cond, color in zip(conditions.values(), palette):
            sns.tsplot(
                X[y.isin(cond), ch],
                time=times,
                color=color,
                n_boot=n_boot,
                ci=ci,
                ax=axes[ch],
            )

        if diff_waveform:
            diff = np.nanmean(X[y == diff_waveform[1], ch], axis=0) - np.nanmean(
                X[y == diff_waveform[0], ch], axis=0
            )
            axes[ch].plot(times, diff, color="k", lw=1)

        axes[ch].set_title(epochs.ch_names[ch])
        axes[ch].set_ylim(ylim)
        axes[ch].axvline(
            x=0, ymin=ylim[0], ymax=ylim[1], color="k", lw=1, label="_nolegend_"
        )

    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("Amplitude (uV)")
    axes[-1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Amplitude (uV)")

    if diff_waveform:
        legend = ["{} - {}".format(diff_waveform[1], diff_waveform[0])] + list(
            conditions.keys()
        )
    else:
        legend = conditions.keys()
    axes[-1].legend(
        legend, bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0.0
    )
    sns.despine()
    plt.tight_layout()

    if title:
        fig.suptitle(title, fontsize=20)

    return fig, axes


def plot_highlight_regions(
    x, y, hue, hue_thresh=0, xlabel="", ylabel="", legend_str=()
):
    """Plot a line with highlighted regions based on additional value.
    Plot a line and highlight ranges of x for which an additional value
    is lower than a threshold. For example, the additional value might be
    pvalues, and the threshold might be 0.05.
    Args:
        x (array_like): x coordinates
        y (array_like): y values of same shape as `x`
    Keyword Args:
        hue (array_like): values to be plotted as hue based on `hue_thresh`.
            Must be of the same shape as `x` and `y`.
        hue_thresh (float): threshold to be applied to `hue`. Regions for which
            `hue` is lower than `hue_thresh` will be highlighted.
        xlabel (str): x-axis label
        ylabel (str): y-axis label
        legend_str (tuple): legend for the line and the highlighted regions
    Returns:
        (matplotlib.figure.Figure): figure object
        (list of matplotlib.axes._subplots.AxesSubplot): list of axes
    """
    fig, axes = plt.subplots(1, 1, figsize=(10, 5), sharey=True)

    axes.plot(x, y, lw=2, c="k")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    kk = 0
    a = []
    while kk < len(hue):
        if hue[kk] < hue_thresh:
            b = kk
            kk += 1
            while kk < len(hue):
                if hue[kk] > hue_thresh:
                    break
                else:
                    kk += 1
            a.append([b, kk - 1])
        else:
            kk += 1

    st = (x[1] - x[0]) / 2.0
    for p in a:
        axes.axvspan(x[p[0]] - st, x[p[1]] + st, facecolor="g", alpha=0.5)
    plt.legend(legend_str)
    sns.despine()

    return fig, axes


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



def check_report(eeg: EEG, n_times: int=60, pause_time=10, thres_std_low=None, thres_std_high=None, n_goods=2,n_inarow=10):
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
    if thres_std_high is None:
        if eeg.device_name in ["ganglion", "ganglion_wifi", "cyton",
                    "cyton_wifi", "cyton_daisy", "cyton_daisy_wifi"]:
            thres_std_high = 9
        elif eeg.device_name in ["notion1", "notion2", "crown"]:
            thres_std_high = 15
        elif 'muse' in eeg.device_name:
            thres_std_high = 18

    if thres_std_low is None:

        if 'muse' in eeg.device_name: 
            thres_std_low = 1

        elif eeg.device_name in ["ganglion", "ganglion_wifi", "cyton",
                                 "cyton_wifi", "cyton_daisy", "cyton_daisy_wifi",
                                 "notion1", "notion2", "crown"]:
            thres_std_low = 1

            
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

            prompt_start = time()
            continue_sigqual = input("\nChecks will resume in %s seconds...Press 'c' (and ENTER key) if you want to stop adjusting for better quality.\n" %pause_time)
            while time() < prompt_start + 5:
                if continue_sigqual == 'c':
                    break
            if continue_sigqual == 'c':
                print("\nStopping signal quality checks!")
                break
        
        sleep(pause_time)



def fix_musemissinglines(orig_f,new_f=''):

    if new_f == '': new_f = orig_f.replace('.csv', '_fml.csv')

    print('writing fixed file to %s' %new_f)

    # Read oriignal file

    F = open(orig_f, 'r')
    Ls = F.readlines()
    newLs = ['' for _ in Ls]
    

    # Correct first line

    l = Ls[0]
    newl = deepcopy(l)
    numcols = len(l.split(','))
    if numcols == 6:
      newl = newl.replace('\n', ',Marker\n')
    newLs[0] = newl


    # Correct the rest

    for l_it,l in enumerate(Ls):
        if l_it!=0:
            numcols = len(l.split(','))
            if numcols==6:
                newline = l.replace('\n', ',0\n')
            else:
                newline = l
            newLs[l_it] = newline


    # Write corrected file

    newF = open(new_f, 'w+')
    newF.writelines(newLs)
    newF.close()
                            
