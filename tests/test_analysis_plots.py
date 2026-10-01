"""
Tests for the plotting helpers in eegnb.analysis.

These run on synthetic MNE epochs, so no EEG hardware and no downloaded
dataset is needed.
"""

from collections import OrderedDict

import matplotlib

matplotlib.use("Agg")

import matplotlib.lines as mlines
import mne
import numpy as np
import pytest

from eegnb.analysis.analysis_utils import plot_conditions


CH_NAMES = ["TP9", "AF7", "AF8", "TP10"]


def _make_epochs(data, codes, sfreq=256.0):
    """Wrap raw arrays into MNE epochs with event codes 1 and 2."""
    info = mne.create_info(CH_NAMES, sfreq, ch_types="eeg")
    n_epochs, _, n_times = data.shape
    events = np.column_stack(
        [np.arange(n_epochs) * n_times, np.zeros(n_epochs, int), codes]
    )
    return mne.EpochsArray(
        data,
        info,
        events=events,
        event_id={"Non-Target": 1, "Target": 2},
        tmin=-0.1,
        verbose="error",
    )


def _noise_epochs(n_epochs=20, n_times=64):
    rng = np.random.RandomState(0)
    data = rng.randn(n_epochs, len(CH_NAMES), n_times) * 1e-6
    codes = np.array([1, 2] * (n_epochs // 2))
    data[codes == 2] += 5e-6
    return _make_epochs(data, codes)


def _legend_entries(ax):
    """Return [(label, rgba of the handle)] for the legend on `ax`."""
    legend = ax.get_legend()
    assert legend is not None, "expected a legend on the last axis"

    entries = []
    for text, handle in zip(legend.get_texts(), legend.legend_handles):
        assert isinstance(
            handle, mlines.Line2D
        ), "legend handles should be lines, not confidence-interval bands"
        entries.append(
            (text.get_text(), tuple(matplotlib.colors.to_rgba(handle.get_color())))
        )
    return entries


@pytest.mark.parametrize("diff_waveform", [None, (1, 2)])
def test_plot_conditions_legend_matches_lines(diff_waveform):
    """Each legend label must sit next to the colour it actually describes.

    Regression test for #226. The legend used to be built from a bare list of
    labels, which matplotlib paired with the artists in draw order. The
    resulting legend named the difference waveform with a condition colour and
    left the black difference line unlabelled.
    """
    epochs = _noise_epochs()
    conditions = OrderedDict(NonTarget=[1], Target=[2])

    import seaborn as sns

    palette = sns.color_palette("hls", len(conditions) + 1)

    _, axes = plot_conditions(
        epochs,
        conditions=conditions,
        diff_waveform=diff_waveform,
        channel_count=4,
        n_boot=10,
    )

    expected = [
        (name, tuple(matplotlib.colors.to_rgba(color)))
        for name, color in zip(conditions.keys(), palette)
    ]
    if diff_waveform:
        expected.append(
            (
                "{} - {}".format(diff_waveform[1], diff_waveform[0]),
                tuple(matplotlib.colors.to_rgba("k")),
            )
        )

    assert _legend_entries(axes[-1]) == expected

    matplotlib.pyplot.close("all")


def test_plot_conditions_plots_the_condition_average():
    """The line drawn per condition must be the average over that condition's
    epochs, not one arbitrary epoch.

    Regression test for #226. The epochs-by-time frame was handed to seaborn in
    wide form with the channel number as `y`, so seaborn selected column number
    `ch` of that frame. Column `ch` is epoch number `ch`, which meant channel 0
    showed epoch 0, channel 1 showed epoch 1, and so on, with no averaging and
    no confidence interval.
    """
    n_epochs, n_times = 8, 16

    # Every epoch is a distinct constant, so the average of a condition and any
    # single epoch of it are all different numbers and cannot be confused.
    data = np.zeros((n_epochs, len(CH_NAMES), n_times))
    for i in range(n_epochs):
        data[i, :, :] = (i + 1) * 1e-6
    codes = np.array([1, 2] * (n_epochs // 2))

    epochs = _make_epochs(data, codes)
    conditions = OrderedDict(NonTarget=[1], Target=[2])

    _, axes = plot_conditions(
        epochs,
        conditions=conditions,
        diff_waveform=None,
        channel_count=len(CH_NAMES),
        n_boot=10,
    )

    # Values are scaled to microvolts inside plot_conditions.
    scaled = data[:, 0, 0] * 1e6
    expected_means = [scaled[codes == code].mean() for code in (1, 2)]

    for ch, ax in enumerate(axes[: len(CH_NAMES)]):
        drawn = [line.get_ydata() for line in ax.get_lines() if len(line.get_ydata()) == n_times]
        assert len(drawn) == len(conditions), (
            f"channel {ch}: expected one line per condition, got {len(drawn)}"
        )
        for ydata, expected in zip(drawn, expected_means):
            assert np.allclose(ydata, expected), (
                f"channel {ch}: plotted {ydata[0]} but the condition average is {expected}"
            )

    matplotlib.pyplot.close("all")
