"""Integration tests for the push_marker() event-marker abstraction.

Covers the runnable, display-free subset:
  1. one shared timestamp across all subscribers (built-in eeg + devices)
  2. optional-subscriber notification + raise_on_error isolation (both directions)
  3. the muse scalar->[marker] wrap guard (back-compat with pre-wrapped lists)

The SSVEP first-flip onset test (#4) and full-paradigm smoke (#5) need a real
PsychoPy window / board and are intentionally not here.
"""

import logging

import pytest

from eegnb.experiments.Experiment import BaseExperiment
from eegnb.devices.eeg import EEG


class FakeEmitter:
    """Stands in for self.eeg / a self.devices entry; records push_sample calls."""

    def __init__(self, log):
        self.log = log

    def push_sample(self, marker, timestamp):
        self.log.append((marker, timestamp))


class _StubExperiment(BaseExperiment):
    """Concrete BaseExperiment: satisfies the ABC without a real paradigm."""

    def load_stimulus(self):
        pass

    def present_stimulus(self, *a, **k):
        pass


def _bare_experiment():
    """A BaseExperiment without running __init__ (no PsychoPy window needed)."""
    exp = object.__new__(_StubExperiment)
    exp.eeg = None
    exp.devices = []
    exp.marker_subscribers = []
    exp._subscriber_failures = {}
    # the built-in essential recorders __init__ would have registered
    exp.subscribe_marker(exp._emit_to_eeg)
    exp.subscribe_marker(exp._emit_to_devices)
    return exp


# 1 ---------------------------------------------------------------------------
def test_push_marker_one_timestamp_across_emitters():
    log = []
    exp = _bare_experiment()
    exp.eeg = FakeEmitter(log)
    exp.devices = [FakeEmitter(log), FakeEmitter(log)]

    exp.push_marker(1, 0)

    assert len(log) == 3                       # eeg + both devices fired
    assert {m for m, _ in log} == {1}          # all got the same marker value
    assert len({t for _, t in log}) == 1       # ...under ONE shared timestamp


def test_push_marker_devices_only_no_eeg():
    log = []
    exp = _bare_experiment()
    exp.devices = [FakeEmitter(log)]
    exp.push_marker(2, 5)
    assert log == [(2, log[0][1])]             # eeg=None tolerated, device still fired


# 2 ---------------------------------------------------------------------------
def test_optional_subscriber_receives_marker_timestamp_trial_idx():
    emit_log, seen = [], []
    exp = _bare_experiment()
    exp.eeg = FakeEmitter(emit_log)
    exp.subscribe_marker(
        lambda marker, timestamp, trial_idx: seen.append((marker, timestamp, trial_idx)),
        raise_on_error=False,
    )

    exp.push_marker(1, 7)

    emitted_ts = emit_log[0][1]
    assert seen == [(1, emitted_ts, 7)]        # subscriber got (marker, same ts, trial_idx)


def test_optional_subscriber_exception_is_isolated(caplog):
    emit_log, seen = [], []
    exp = _bare_experiment()
    exp.eeg = FakeEmitter(emit_log)

    def boom(marker, timestamp, trial_idx):
        raise RuntimeError("bad observer")

    exp.subscribe_marker(boom, raise_on_error=False)
    exp.subscribe_marker(
        lambda marker, timestamp, trial_idx: seen.append((trial_idx, timestamp)),
        raise_on_error=False,
    )

    with caplog.at_level(logging.ERROR):
        exp.push_marker(1, 3)                  # must NOT raise

    assert emit_log, "emitter still fired despite a failing optional subscriber"
    assert seen == [(3, emit_log[0][1])]       # later subscriber still ran
    assert "marker subscriber failed" in caplog.text


def test_repeated_optional_failure_logs_once(caplog):
    """A subscriber failing every trial logs its traceback once, but counts all failures."""
    exp = _bare_experiment()
    exp.eeg = FakeEmitter([])

    def boom(marker, timestamp, trial_idx):
        raise RuntimeError("bad observer")

    exp.subscribe_marker(boom, raise_on_error=False)

    with caplog.at_level(logging.ERROR):
        for i in range(3):
            exp.push_marker(1, i)

    logged = [r for r in caplog.records if "suppressing further tracebacks" in r.getMessage()]
    assert len(logged) == 1                    # logged once across 3 failures
    assert exp._subscriber_failures[boom] == 3 # ...but all counted


def test_raise_on_error_subscriber_propagates_and_halts():
    """An essential (raise_on_error=True) subscriber that raises aborts the dispatch:
    the exception propagates and later subscribers do not run."""
    exp = _bare_experiment()
    seen = []

    def boom(marker, timestamp, trial_idx):
        raise RuntimeError("board died")

    exp.subscribe_marker(boom, raise_on_error=True)
    exp.subscribe_marker(
        lambda marker, timestamp, trial_idx: seen.append(trial_idx), raise_on_error=False
    )

    with pytest.raises(RuntimeError, match="board died"):
        exp.push_marker(1, 0)
    assert seen == [], "subscribers after a raise_on_error failure do not run"


# 3 ---------------------------------------------------------------------------
class FakeOutlet:
    def __init__(self):
        self.last = None

    def push_sample(self, marker, timestamp):
        self.last = marker


def _bare_eeg(outlet):
    eeg = object.__new__(EEG)
    eeg.muse_StreamOutlet = outlet
    return eeg


def test_muse_wraps_scalar_marker():
    outlet = FakeOutlet()
    eeg = _bare_eeg(outlet)
    eeg._muse_push_sample(2, 123.0)
    assert outlet.last == [2]                  # scalar -> single-channel vector


def test_muse_passes_prewrapped_list_unchanged():
    outlet = FakeOutlet()
    eeg = _bare_eeg(outlet)
    eeg._muse_push_sample([2], 123.0)          # P300 back-compat path
    assert outlet.last == [2]                  # no double-wrap
