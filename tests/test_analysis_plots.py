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


def _make_epochs(data, codes, sfreq=256.0, event_id=None):
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
        event_id=event_id if event_id is not None else {"Non-Target": 1, "Target": 2},
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


@pytest.mark.parametrize("diff_waveform", [None, (1, 2), ("Non-Target", "Target")])
def test_plot_conditions_legend_matches_lines(diff_waveform):
    """Each legend label matches its line colour."""
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


@pytest.mark.parametrize("markers", [(1, 2), ("Non-Target", "Target"), (1, "Target")])
def test_plot_conditions_plots_the_condition_average(markers):
    """Each condition's plotted waveform matches its epoch average."""
    n_epochs, n_times = 8, 16

    data = np.zeros((n_epochs, len(CH_NAMES), n_times))
    for i in range(n_epochs):
        data[i, :, :] = (i + 1) * 1e-6
    codes = np.array([1, 2] * (n_epochs // 2))

    epochs = _make_epochs(data, codes)
    conditions = OrderedDict(NonTarget=[markers[0]], Target=[markers[1]])

    _, axes = plot_conditions(
        epochs,
        conditions=conditions,
        diff_waveform=None,
        channel_count=len(CH_NAMES),
        n_boot=10,
    )

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


def test_plot_conditions_names_match_numeric_waveforms():
    epochs = _noise_epochs()
    named_conditions = OrderedDict(NonTarget=["Non-Target"], Target=["Target"])
    numeric_conditions = OrderedDict(NonTarget=[1], Target=[2])
    numeric_fig, numeric_axes = plot_conditions(
        epochs, conditions=numeric_conditions, diff_waveform=(1, 2), n_boot=10
    )
    named_fig, named_axes = plot_conditions(
        epochs,
        conditions=named_conditions,
        diff_waveform=("Non-Target", "Target"),
        n_boot=10,
    )
    try:
        expected_difference = epochs.get_data()[epochs.events[:, -1] == 2].mean(axis=0)
        expected_difference -= epochs.get_data()[epochs.events[:, -1] == 1].mean(axis=0)
        for ch, (numeric_ax, named_ax) in enumerate(zip(numeric_axes, named_axes)):
            numeric_lines = [line for line in numeric_ax.lines if len(line.get_xdata()) == len(epochs.times)]
            named_lines = [line for line in named_ax.lines if len(line.get_xdata()) == len(epochs.times)]
            assert len(numeric_lines) == len(named_lines) == 3
            for numeric_line, named_line in zip(numeric_lines, named_lines):
                np.testing.assert_allclose(named_line.get_xdata(), epochs.times)
                np.testing.assert_allclose(named_line.get_ydata(), numeric_line.get_ydata())
            np.testing.assert_allclose(named_lines[2].get_ydata(), expected_difference[ch] * 1e6)
        assert named_conditions == OrderedDict(NonTarget=["Non-Target"], Target=["Target"])
    finally:
        matplotlib.pyplot.close(numeric_fig)
        matplotlib.pyplot.close(named_fig)


def test_plot_conditions_grouped_cueing_difference():
    rng = np.random.RandomState(1)
    codes = np.array([11, 12, 21, 22, 21, 11, 22, 12])
    data = rng.randn(8, len(CH_NAMES), 16) * 1e-6
    data += codes[:, None, None] * 1e-6
    epochs = _make_epochs(data, codes, event_id={
        "InvalidTarget_Left": 11, "InvalidTarget_Right": 12,
        "ValidTarget_Left": 21, "ValidTarget_Right": 22,
    })
    conditions = OrderedDict(
        ValidTarget=["ValidTarget_Left", "ValidTarget_Right"],
        InvalidTarget=["InvalidTarget_Left", "InvalidTarget_Right"],
    )
    fig, axes = plot_conditions(
        epochs, conditions=conditions,
        diff_waveform=("ValidTarget", "InvalidTarget"), n_boot=10,
    )
    try:
        valid = data[np.isin(codes, [21, 22])].mean(axis=0) * 1e6
        invalid = data[np.isin(codes, [11, 12])].mean(axis=0) * 1e6
        for ch, ax in enumerate(axes):
            drawn = [line.get_ydata() for line in ax.lines if len(line.get_xdata()) == len(epochs.times)]
            assert len(drawn) == 3
            np.testing.assert_allclose(drawn[0], valid[ch])
            np.testing.assert_allclose(drawn[1], invalid[ch])
            np.testing.assert_allclose(drawn[2], invalid[ch] - valid[ch])
        assert _legend_entries(axes[-1])[-1][0] == "InvalidTarget - ValidTarget"
    finally:
        matplotlib.pyplot.close(fig)


@pytest.mark.parametrize(
    "conditions, diff_waveform",
    [
        (OrderedDict(Unknown=["missing"]), None),
        (OrderedDict(NonTarget=[1], Target=[2]), ("Non-Target", "missing")),
    ],
)
def test_plot_conditions_unknown_name_raises(conditions, diff_waveform):
    with pytest.raises(ValueError, match="Unknown event name: 'missing'"):
        plot_conditions(_noise_epochs(), conditions=conditions, diff_waveform=diff_waveform)
