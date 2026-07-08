"""Tests for BaseExperiment.push_marker()."""

import logging

import pytest

from eegnb.experiments.Experiment import BaseExperiment


class Recorder:
    """Fake eeg / device: remembers every push_sample(marker, timestamp)."""

    def __init__(self):
        self.calls = []

    def push_sample(self, marker, timestamp):
        self.calls.append((marker, timestamp))


class StubExperiment(BaseExperiment):
    """Minimal concrete BaseExperiment — no real stimulus, opens no window."""

    def load_stimulus(self):
        pass

    def present_stimulus(self, idx):
        pass


@pytest.fixture
def exp():
    # Real __init__ runs (it opens no window) and registers the two built-in
    # subscribers that write the marker to self.eeg and self.devices.
    return StubExperiment("test", duration=1, eeg=None, save_fn=None,
                          n_trials=1, iti=0, soa=0, jitter=0)


def boom(marker, timestamp, trial_idx):
    raise RuntimeError("boom")


def test_marker_reaches_eeg_and_every_device_under_one_timestamp(exp):
    exp.eeg = Recorder()
    exp.devices = [Recorder(), Recorder()]

    exp.push_marker(1)

    ts = exp.eeg.calls[0][1]              # the single timestamp push_marker minted
    for s in [exp.eeg, *exp.devices]:
        assert s.calls == [(1, ts)]       # each sink recorded marker 1 at that timestamp


def test_push_marker_tolerates_no_eeg(exp):
    exp.devices = [Recorder()]                # exp.eeg stays None

    exp.push_marker(2)                        # must not crash on eeg=None

    assert exp.devices[0].calls[0][0] == 2


def test_failing_optional_subscriber_does_not_stop_the_others(exp, caplog):
    exp.eeg = Recorder()
    seen = []
    exp.subscribe_marker(boom, raise_on_error=False)
    exp.subscribe_marker(lambda *args: seen.append(args), raise_on_error=False)

    with caplog.at_level(logging.ERROR):
        exp.push_marker(1, trial_idx=3)       # boom is swallowed, not raised

    ts = exp.eeg.calls[0][1]
    assert exp.eeg.calls == [(1, ts)]         # essential subscriber still wrote the marker
    assert seen == [(1, ts, 3)]               # later optional subscriber still ran
    assert "marker subscriber failed" in caplog.text


def test_repeatedly_failing_subscriber_logs_once_but_counts_all(exp, caplog):
    exp.subscribe_marker(boom, raise_on_error=False)

    with caplog.at_level(logging.ERROR):
        for i in range(3):
            exp.push_marker(1, trial_idx=i)

    logged = [r for r in caplog.records if "suppressing further tracebacks" in r.getMessage()]
    assert len(logged) == 1                   # traceback logged once...
    assert exp._subscriber_failures[boom] == 3  # ...but every failure counted


def test_essential_subscriber_failure_propagates_and_halts_dispatch(exp):
    seen = []
    exp.subscribe_marker(boom, raise_on_error=True)     # essential: failure must surface
    exp.subscribe_marker(lambda *args: seen.append(args), raise_on_error=False)

    with pytest.raises(RuntimeError, match="boom"):
        exp.push_marker(1)
    assert seen == []                         # dispatch aborted; later subscriber never ran
