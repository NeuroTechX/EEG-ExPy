"""
Tests for plot_conditions in eegnb.analysis.utils.

These run on synthetic MNE epochs, so no EEG hardware and no downloaded
dataset is needed.
"""

from collections import OrderedDict

import matplotlib

matplotlib.use("Agg")

import mne
import numpy as np
import pytest

from eegnb.analysis.utils import plot_conditions

CH_NAMES = ["TP9", "AF7", "AF8", "TP10"]
N_EPOCHS = 20
N_TIMES = 32

# Flat epochs with one exact amplitude per condition, in volts, so that every
# plotted value has a single unambiguous correct answer.
NON_TARGET_UV = 2.0
TARGET_UV = 5.0


def _make_epochs():
    data = np.zeros((N_EPOCHS, len(CH_NAMES), N_TIMES))
    codes = np.array([1, 2] * (N_EPOCHS // 2))
    data[codes == 1] = NON_TARGET_UV * 1e-6
    data[codes == 2] = TARGET_UV * 1e-6

    events = np.column_stack(
        [np.arange(N_EPOCHS) * N_TIMES, np.zeros(N_EPOCHS, int), codes]
    )
    return mne.EpochsArray(
        data,
        mne.create_info(CH_NAMES, 256.0, ch_types="eeg"),
        events=events,
        event_id={"Non-Target": 1, "Target": 2},
        tmin=-0.1,
        verbose="error",
    )


def _data_lines(ax):
    return [line for line in ax.get_lines() if len(line.get_ydata()) == N_TIMES]


@pytest.fixture
def conditions():
    return OrderedDict(NonTarget=[1], Target=[2])


def test_plot_conditions_runs_with_default_diff_waveform(conditions):
    """The documented default must not raise.

    `diff_waveform` defaults to the marker codes (1, 2), but the difference
    waveform used to look them up as condition dict keys, so simply calling
    plot_conditions(epochs, conditions) raised KeyError: 2.
    """
    fig, axes = plot_conditions(
        _make_epochs(), conditions=conditions, channel_count=len(CH_NAMES), n_boot=10
    )
    assert fig is not None
    matplotlib.pyplot.close("all")


def test_plot_conditions_draws_each_condition(conditions):
    """Every condition must actually be drawn.

    Rows were selected with `dfX.condition.isin(<marker codes>)`, but the
    condition column produced by `epochs.to_data_frame()` holds event *names*.
    Nothing matched, so each subplot came out empty.
    """
    _, axes = plot_conditions(
        _make_epochs(),
        conditions=conditions,
        diff_waveform=None,
        channel_count=len(CH_NAMES),
        n_boot=10,
    )

    for ch, ax in enumerate(axes[: len(CH_NAMES)]):
        assert len(_data_lines(ax)) == len(conditions), (
            f"channel {ch}: expected one line per condition, got "
            f"{len(_data_lines(ax))}"
        )

    matplotlib.pyplot.close("all")


def test_plot_conditions_amplitudes_are_in_microvolts(conditions):
    """Plotted values must be microvolts, and the difference must be correct.

    `to_data_frame()` already scales EEG from volts to microvolts, so the
    extra `*= 1e6` pushed every trace a millionfold outside the default
    ylim of (-6, 6).
    """
    _, axes = plot_conditions(
        _make_epochs(), conditions=conditions, channel_count=len(CH_NAMES), n_boot=10
    )

    expected = [NON_TARGET_UV, TARGET_UV, TARGET_UV - NON_TARGET_UV]

    for ch, ax in enumerate(axes[: len(CH_NAMES)]):
        lines = _data_lines(ax)
        assert len(lines) == len(expected), f"channel {ch}: missing traces"
        for line, value in zip(lines, expected):
            assert np.allclose(line.get_ydata(), value), (
                f"channel {ch}: plotted {line.get_ydata()[0]} uV, expected {value} uV"
            )

    matplotlib.pyplot.close("all")
