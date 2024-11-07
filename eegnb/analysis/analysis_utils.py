import copy
from copy import deepcopy
import math
import logging
import sys
from collections import OrderedDict
from glob import glob
from typing import Union, List
from time import sleep, time
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
#from eegnb.devices.eeg import EEG
from eegnb.devices.utils import EEG_INDICES, SAMPLE_FREQS


# this should probably not be done here
sns.set_context("talk")
sns.set_style("white")


logger = logging.getLogger(__name__)


# Empirically determined lower and upper bounds of 
# acceptable temporal standard deviations 
# for different EEG devices tested by us
openbci_devices = ['ganglion', 'ganglion_wifi', 'cyton', 'cyton_wifi', 'cyton_daisy_wifi']
muse_devices = ['muse' + model + sfx for model in ['2016', '2', 'S'] for sfx in ['', '_bfn', '_bfb']]
neurosity_devices = ['notion1', 'notion2', 'crown']
gtec_devices = ['unicorn']
alltesteddevices = openbci_devices + muse_devices + neurosity_devices + gtec_devices
thres_stds = {}
for device in alltesteddevices: 
    if device in openbci_devices: thres_stds[device] = [1,9]
    elif device in muse_devices: thres_stds[device] = [1,18]
    elif device in neurosity_devices: thres_stds[device] = [1,15]
    elif device in gtec_devices: thres_stds[device] = [1,15]


def load_csv_as_raw(
    fnames: List[str],
    sfreq: float,
    ch_ind,
    aux_ind=None,
    replace_ch_names=None,
    verbose=1,
    resp_on_missing='warn'
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


    print('\n\nLoading these files: \n')
    for f in fnames: print(f + '\n')
    print('\n\n')


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
    raws.set_montage(montage,on_missing=resp_on_missing)

    return raws


def load_data(
    subject: Union[str, int],
    session: Union[str, int],
    device_name: str,
    experiment: str,
    replace_ch_names=None,
    verbose=1,
    site="local",
    data_dir=None,
    inc_chans=None
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
        subject (int or str): subject number. If 'all', load all
            subjects.
        session (int or str): session number. If 'all', load all
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

    subject_int = int(subject)
    session_int = int(session)

    subject_str = "*" if subject == "all" else f"subject{subject_int:04}"
    session_str = "*" if session == "all" else f"session{session_int:03}"

    recdir = _get_recording_dir(device_name, experiment, subject_str, session_str, site)#, data_dir)
    data_path = os.path.join(data_dir, recdir, "*.csv")

    fnames = glob(str(data_path))

    if len(fnames) == 0:
        raise Exception("No filenames found in folder: %s" %data_path)


    sfreq = SAMPLE_FREQS[device_name]

    ch_ind = EEG_INDICES[device_name]

    if inc_chans is not None:
        ch_ind = inc_chans

    if device_name in ["muse2016", "muse2", "museS"]:
        aux_ind = [5]
    else:
        aux_ind = None

    res = load_csv_as_raw(
            fnames,
            sfreq=sfreq,
            ch_ind=ch_ind,
            aux_ind=aux_ind,
            replace_ch_names=replace_ch_names,
            verbose=verbose)

    return res


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
    channel_order=None,
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

    if channel_order:
        channel_order = np.array(channel_order)
    else:
        channel_order = np.array(range(channel_count))

    if isinstance(conditions, dict):
        conditions = OrderedDict(conditions)

    if palette is None:
        palette = sns.color_palette("hls", len(conditions) + 1)

    X = epochs.get_data() * 1e6

    X = X[:, channel_order]

    times = epochs.times
    y = pd.Series(epochs.events[:, -1])

    midaxis = math.ceil(channel_count / 2)
    fig, axes = plt.subplots(2, midaxis, figsize=[12, 6], sharex=True, sharey=False)

    # get individual plot axis
    plot_axes = []
    for axis_y in range(midaxis):
        for axis_x in range(2):
            plot_axes.append(axes[axis_x, axis_y])
    axes = plot_axes

    for ch in range(channel_count):
        for cond, color in zip(conditions.values(), palette):
            sns.lineplot(
                data=pd.DataFrame(X[y.isin(cond), ch].T, index=times),
                x=times,
                y=ch,
                color=color,
                n_boot=n_boot,
                ax=axes[ch],
                errorbar=('ci',ci)
            )
        axes[ch].set(xlabel='Time (s)', ylabel='Amplitude (uV)', title=epochs.ch_names[channel_order[ch]])

        if diff_waveform:
            diff = np.nanmean(X[y == diff_waveform[1], ch], axis=0) - np.nanmean(
                X[y == diff_waveform[0], ch], axis=0
            )
            axes[ch].plot(times, diff, color="k", lw=1)

        axes[ch].set_title(epochs.ch_names[channel_order[ch]])
        axes[ch].set_ylim(ylim)
        axes[ch].axvline(
            x=0, ymin=ylim[0], ymax=ylim[1], color="k", lw=1, label="_nolegend_"
        )

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








def fix_musemissinglines(orig_f,new_f=''):

    #if new_f == '': new_f = orig_f.replace('.csv', '_fml.csv')

    # Overwriting 
    new_f = orig_f

    print('writing fixed file to %s' %new_f)

    # Read original file

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
                            
