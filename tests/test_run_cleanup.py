import pytest
from types import SimpleNamespace

pytest.importorskip("psychopy")

from eegnb.experiments.Experiment import BaseExperiment
from eegnb.experiments.BlockExperiment import BlockExperiment


class _Recorder:
    backend = "brainflow"

    def __init__(self):
        self.started = False
        self.stopped = False

    def start(self, fn, duration=None):
        self.started = True

    def stop(self):
        self.stopped = True


def _experiment(base, fail, use_vr=False, **kwargs):
    state = SimpleNamespace(draws=0, closed=False, telemetry=None)

    class _Experiment(base):
        def load_stimulus(self):
            pass

        def present_stimulus(self, idx):
            pass

        def setup(self, instructions=True):
            self.window = SimpleNamespace(close=lambda: setattr(state, "closed", True))
            self.vr = SimpleNamespace(
                sync_vr_clock=lambda: None,
                save_telemetry=lambda fn: setattr(state, "telemetry", fn))
            return True

        def _draw(self, present_stimulus):
            state.draws += 1
            if state.draws >= 3:
                raise fail

        def _clear_user_input(self):
            pass

        def _user_input(self, input_type):
            return False

        def _show_block_instructions(self, block_index):
            return True

    eeg = _Recorder()
    exp = _Experiment(eeg=eeg, save_fn="recording.csv",
                      iti=0.0, soa=0.01, jitter=0.0, **kwargs)
    exp.use_vr = use_vr
    return exp, eeg, state


CASES = [
    (BaseExperiment, dict(exp_name="t", duration=2, n_trials=5)),
    (BlockExperiment, dict(exp_name="t", block_duration=2, block_trial_size=5, n_blocks=1)),
]


@pytest.mark.parametrize("base, kwargs", CASES, ids=["BaseExperiment", "BlockExperiment"])
@pytest.mark.parametrize("fail", [
    RuntimeError("stimulus failed mid-run"),
    KeyboardInterrupt(),
], ids=["RuntimeError", "KeyboardInterrupt"])
def test_run_stops_the_recording_when_the_trial_loop_raises(base, kwargs, fail):
    exp, eeg, state = _experiment(base, fail, **kwargs)
    with pytest.raises(type(fail)):
        exp.run(instructions=False)
    assert eeg.started
    assert eeg.stopped
    assert state.closed


@pytest.mark.parametrize("base, kwargs", CASES, ids=["BaseExperiment", "BlockExperiment"])
@pytest.mark.parametrize("fail", [
    RuntimeError("stimulus failed mid-run"),
    KeyboardInterrupt(),
], ids=["RuntimeError", "KeyboardInterrupt"])
def test_run_saves_the_vr_telemetry_when_the_trial_loop_raises(base, kwargs, fail):
    exp, eeg, state = _experiment(base, fail, use_vr=True, **kwargs)
    with pytest.raises(type(fail)):
        exp.run(instructions=False)
    assert eeg.stopped
    assert state.telemetry == "recording.csv"
    assert state.closed
