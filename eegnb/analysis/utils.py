from glob import glob
import os
import copy
import math
from collections import OrderedDict

from mne import create_info, concatenate_raws
from mne.io import RawArray
from mne.channels import make_standard_montage
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt

from eegnb import DATA_DIR
from eegnb.devices.utils import EEG_INDICES, SAMPLE_FREQS


sns.set_context('talk')
sns.set_style('white')


def load_csv_as_raw(fnames, sfreq, ch_ind, aux_ind=None,
                    replace_ch_names=None, verbose=1):
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
        ch_names = [list(data.columns)[i] for i in ch_ind] + ['stim']
        print(ch_names)
        ch_types = ['eeg'] * n_eeg + ['misc'] * n_aux + ['stim']

        if replace_ch_names is not None:
            ch_names = [c if c not in replace_ch_names.keys()
                        else replace_ch_names[c] for c in ch_names]

        # Transpose EEG data and convert from uV to Volts
        data = data.values[:, ch_ind + [-1]].T
        data[:-1] *= 1e-6

        # create MNE object
        info = create_info(ch_names=ch_names, ch_types=ch_types, sfreq=sfreq,
                           verbose=1)
        raw.append(RawArray(data=data, info=info, verbose=verbose))

    raws = concatenate_raws(raw, verbose=verbose)
    montage = make_standard_montage('standard_1005')
    raws.set_montage(montage)

    return raws


def load_data(subject_id, session_nb, device_name, experiment,
              replace_ch_names=None, verbose=1, site='local', data_dir=None):
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

    if subject_id == 'all':
        subject_str = 'subject*'
    else:
        subject_str = 'subject%04.f' % subject_id

    if session_nb == 'all':
        session_str = 'session*'
    else:
        session_str = 'session%03.f' % session_nb

    if site == 'all':
        site = '*'

    if data_dir is None:
      data_dir = DATA_DIR

    data_path = os.path.join(data_dir, experiment, site, device_name,
                             subject_str, session_str, '*.csv')
    fnames = glob(data_path)

    sfreq = SAMPLE_FREQS[device_name]
    ch_ind = EEG_INDICES[device_name]
    if device_name in ['muse2016', 'muse2', 'museS']:
        return load_csv_as_raw(
            fnames,
            sfreq=sfreq,
            ch_ind=ch_ind,
            aux_ind=[5],
            replace_ch_names=replace_ch_names,
            verbose=verbose
        )
    else:
        return load_csv_as_raw(
            fnames,
            sfreq=sfreq,
            ch_ind=ch_ind,
            replace_ch_names=replace_ch_names,
            verbose=verbose
        )


def plot_conditions(epochs, conditions=OrderedDict(), ci=97.5, n_boot=1000,
                    title='', palette=None, ylim=(-6, 6),
                    diff_waveform=(1, 2), channel_count=4):
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

    midaxis = math.ceil(channel_count/2)
    fig, axes = plt.subplots(2, midaxis, figsize=[12, 6],
                             sharex=True, sharey=True)

    # get individual plot axis
    plot_axes = []
    for axis_y in range(midaxis):
        for axis_x in range(2):
            plot_axes.append(axes[axis_x, axis_y])
    axes = plot_axes

    for ch in range(channel_count):
        for cond, color in zip(conditions.values(), palette):
            sns.tsplot(X[y.isin(cond), ch], time=times, color=color,
                       n_boot=n_boot, ci=ci, ax=axes[ch])

        if diff_waveform:
            diff = (np.nanmean(X[y == diff_waveform[1], ch], axis=0) -
                    np.nanmean(X[y == diff_waveform[0], ch], axis=0))
            axes[ch].plot(times, diff, color='k', lw=1)

        axes[ch].set_title(epochs.ch_names[ch])
        axes[ch].set_ylim(ylim)
        axes[ch].axvline(x=0, ymin=ylim[0], ymax=ylim[1], color='k',
                         lw=1, label='_nolegend_')

    axes[0].set_xlabel('Time (s)')
    axes[0].set_ylabel('Amplitude (uV)')
    axes[-1].set_xlabel('Time (s)')
    axes[1].set_ylabel('Amplitude (uV)')

    if diff_waveform:
        legend = (['{} - {}'.format(diff_waveform[1], diff_waveform[0])] +
                  list(conditions.keys()))
    else:
        legend = conditions.keys()
    axes[-1].legend(legend, bbox_to_anchor=(1.05, 1), loc='upper left',
                    borderaxespad=0.)
    sns.despine()
    plt.tight_layout()

    if title:
        fig.suptitle(title, fontsize=20)

    return fig, axes


def plot_highlight_regions(x, y, hue, hue_thresh=0, xlabel='', ylabel='',
                           legend_str=()):
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

    axes.plot(x, y, lw=2, c='k')
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
        axes.axvspan(x[p[0]]-st, x[p[1]]+st, facecolor='g', alpha=0.5)
    plt.legend(legend_str)
    sns.despine()

    return fig, axes
