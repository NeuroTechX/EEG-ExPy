from glob import glob
import os
import copy
import math
from collections import OrderedDict
from typing import Union, List

from mne import create_info, concatenate_raws
from mne.io import RawArray
from mne.channels import make_standard_montage
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt

from eegnb import _get_recording_dir
from eegnb.devices.utils import EEG_INDICES, SAMPLE_FREQS


sns.set_context("talk")
sns.set_style("white")


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
        _get_recording_dir(device_name, experiment, subject_str, session_str, site)
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


# From     https://github.com/ErikBjare/thesis/blob/master/src/eegwatch/devices/base.py 
# -------


import logging
from typing import List, Dict
from abc import ABCMeta, abstractmethod

import numpy as np


logger = logging.getLogger(__name__)


def _check_samples(
    buffer: np.ndarray, channels: List[str], max_uv_abs=200
) -> Dict[str, bool]:
    # TODO: Better signal quality check
    chmax = dict(zip(channels, np.max(np.abs(buffer), axis=0)))
    return {ch: maxval < max_uv_abs for ch, maxval in chmax.items()}


def test_check_samples():
    buffer = np.array([[9.0, 11.0, -5, -13]])
    assert {"TP9": True, "AF7": False, "AF8": True, "TP10": False} == _check_samples(
        buffer, channels=["TP9", "AF7", "AF8", "TP10"], max_uv_abs=10
    )


# From    https://github.com/ErikBjare/thesis/blob/master/src/eegclassify/clean.py
# ------

import logging
from typing import List, Optional

import pandas as pd
import numpy as np
from mne.filter import create_filter
from scipy.signal import lfilter, lfilter_zi

#from eegwatch.devices.base import _check_samples # this function is defined above instead

logger = logging.getLogger(__name__)


MAX_UV_ABS_DEFAULT = 400


def clean(df: pd.DataFrame) -> pd.DataFrame:
    # TODO: Add notch filters for 50Hz and 60Hz?
    df = _clean_short(df)
    df = _clean_duplicate_samples(df)
    df = _clean_signal_quality(df)
    df = _clean_inconsistent_sampling(df)
    return df


def filter(
    X: np.ndarray,
    sfreq: float = 250,
    n_chans: int = 4,
    low: float = 3,
    high: float = 40,
    verbose: bool = False 
) -> np.ndarray:
    """Inspired by viewer_v2.py in muse-lsl"""
    window = 10
    n_samples = int(sfreq * window)
    data_f = np.zeros((n_samples, n_chans))

    af = [1.0]
    bf = create_filter(data_f.T, sfreq, low, high, method="fir",verbose=verbose)

    zi = lfilter_zi(bf, af)
    filt_state = np.tile(zi, (n_chans, 1)).transpose()
    filt_samples, filt_state = lfilter(bf, af, X, axis=0, zi=filt_state)

    return filt_samples


def _clean_short(df: pd.DataFrame) -> pd.DataFrame:
    sfreq = 250  # NOTE: Will be different for different devices
    bads = []
    for i, row in df.iterrows():
        samples = len(row["raw_data"])
        seconds = samples / sfreq
        duration = row["stop"] - row["start"]
        if seconds < 0.95 * duration.total_seconds():
            # logger.warning(
            #     f"Bad row found, only had {seconds}s of data out of {duration.total_seconds()}s"
            # )
            bads.append(i)

    logger.warning(f"Dropping {len(bads)} rows due to missing samples")
    return df.drop(bads)


def _clean_duplicate_samples(df: pd.DataFrame) -> pd.DataFrame:
    bads = []
    for i, row in df.iterrows():
        timestamps = [sample[0] for sample in row["raw_data"]]

        # Check for duplicate timestamps
        if len(timestamps) != len(set(timestamps)):
            bads.append(i)

    logger.warning(f"Dropping {len(bads)} bad rows due to duplicate samples")
    return df.drop(bads)


def _clean_inconsistent_sampling(df: pd.DataFrame) -> pd.DataFrame:
    bads = []
    for i, row in df.iterrows():
        timestamps = [sample[0] for sample in row["raw_data"]]

        # Check for consistent sampling
        diffs = np.diff(timestamps)
        if max(diffs) > 2 * min(diffs):
            bads.append(i)

    logger.warning(f"Dropping {len(bads)} bad rows due to inconsistent sampling")
    return df.drop(bads)


def _check_row_signal_quality(
    s: pd.Series, max_uv_abs: float = MAX_UV_ABS_DEFAULT
) -> bool:
    """Takes a single row as input, returns true if good signal quality else false"""
    # TODO: Improve quality detection
    buffer = np.array([t[1:] for t in s["raw_data"]])  # strip timestamp
    channels = [str(i) for i in range(buffer.size)]
    return all(_check_samples(buffer, channels, max_uv_abs).values())


def _row_stats(s: pd.Series):
    buffer = np.array([t[1:] for t in s["raw_data"]])  # strip timestamp
    return {
        "min": np.min(np.abs(buffer), axis=0),
        "max": np.max(np.abs(buffer), axis=0),
        "ok": _check_row_signal_quality(s),
    }


def _clean_signal_quality(
    df: pd.DataFrame, max_uv_abs: float = MAX_UV_ABS_DEFAULT
) -> pd.DataFrame:
    bads = []
    for i, row in df.iterrows():
        # print(_row_stats(row))
        if not _check_row_signal_quality(row, max_uv_abs):
            bads.append(i)

    logger.warning(f"Dropping {len(bads)} bad rows due to bad signal quality")
    return df.drop(bads)


def test_clean_signal_quality():
    df = pd.DataFrame(
        [
            {"raw_data": [[1, 100]]},
            {"raw_data": [[1, 100]]},
            {"raw_data": [[1, 300]]},
        ]
    )
    df_clean = _clean_signal_quality(df, max_uv_abs=200)
    assert len(df_clean) == 2


def _select_classes(
    df: pd.DataFrame,
    col: str,
    classes: List[str],
) -> pd.DataFrame:
    """
    Removes rows that don't match the selected classes.
    """
    return df.loc[df[col].isin(classes), :]


def test_select_classes():
    df = pd.DataFrame({"class": ["a", "a", "b", "c"]})
    df["class"] = df["class"].astype("category")
    df = _select_classes(df, "class", ["a", "b"])
    assert len(df) == 3


def _remove_rare(
    df: pd.DataFrame,
    col: str,
    threshold_perc: Optional[float] = None,
    threshold_count: Optional[int] = None,
) -> pd.DataFrame:
    """
    Removes rows with rare categories.

    based on: https://stackoverflow.com/a/31502730/965332
    """
    if threshold_perc is None and threshold_count is None:
        raise ValueError

    logger.info(
        f"Removing rare classes... (perc: {threshold_perc}, count: {threshold_count})"
    )
    if threshold_count is not None:
        counts = df[col].value_counts()
        df = df.loc[df[col].isin(counts[counts >= threshold_count].index), :]
    if threshold_perc is not None:
        counts = df[col].value_counts(normalize=True)
        df = df.loc[df[col].isin(counts[counts >= threshold_perc].index), :]

    return df


def test_remove_rare():
    df = pd.DataFrame({"class": ["a"] * 10 + ["b"] * 5 + ["c"] * 3 + ["d"] * 2})
    df["class"] = df["class"].astype("category")

    # Remove single class with percent
    assert len(_remove_rare(df, "class", threshold_perc=0.15)) == 18

    # Remove single class with count
    assert len(_remove_rare(df, "class", threshold_count=3)) == 18

    # Remove one class by count and one by percent
    assert len(_remove_rare(df, "class", threshold_perc=0.2, threshold_count=3)) == 15
















