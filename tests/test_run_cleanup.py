import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("psychopy")

from eegnb.experiments.Experiment import BaseExperiment
from eegnb.experiments.BlockExperiment import BlockExperiment
from test_vr_window import _bare, _views_apart


class _Recorder:
    backend = "brainflow"

    def __init__(self):
        self.started = False
        self.stopped = False

    def start(self, fn, duration=None):
        self.started = True

    def stop(self):
        self.stopped = True


VR_SUMMARY = {"backend": "openxr", "stimulus_distance_m": 1.0, "missed_vsyncs": np.int64(3),
              "runtime_to_wallclock_offset_s": np.float64(1.5e9),
              "longest_step_ms": float("nan"), "eye_size_px": np.array([1616, 1648]),
              "manifest": Path("oculus.json")}


def _experiment(base, fail, save_fn, use_vr=False, cancel_after=None, cancel_block=False,
                summary=None, **kwargs):
    state = SimpleNamespace(draws=0, closed=False, timing=None, eye_checks=0)

    def session_summary():
        if isinstance(summary, BaseException):
            raise summary
        return VR_SUMMARY if summary is None else summary

    class _Experiment(base):
        def load_stimulus(self):
            pass

        def present_stimulus(self, idx):
            pass

        def setup(self, instructions=True):
            self.window = SimpleNamespace(close=lambda: setattr(state, "closed", True))
            self.vr = SimpleNamespace(
                sync_vr_clock=lambda: None,
                check_eye_separation=lambda: setattr(state, "eye_checks", state.eye_checks + 1),
                get_session_summary=session_summary,
                save_timing=lambda fn: setattr(state, "timing", fn))
            return True

        def _draw(self, present_stimulus):
            state.draws += 1
            if fail is not None and state.draws >= 3:
                raise fail

        def _clear_user_input(self):
            pass

        def _user_input(self, input_type):
            return (input_type == "cancel" and cancel_after is not None
                    and state.draws >= cancel_after)

        def _show_block_instructions(self, block_index):
            return not cancel_block

    eeg = _Recorder()
    exp = _Experiment(eeg=eeg, save_fn=save_fn, iti=0.0, soa=0.01, jitter=0.0, **kwargs)
    exp.use_vr = use_vr
    return exp, eeg, state


def _session(tmp_path):
    text = (tmp_path / "recording_session.json").read_text(encoding="utf-8")
    return json.loads(text, parse_constant=lambda name: pytest.fail(f"{name} in the JSON"))


CASES = [
    (BaseExperiment, dict(exp_name="t", duration=2, n_trials=5)),
    (BlockExperiment, dict(exp_name="t", block_duration=2, block_trial_size=5, n_blocks=1)),
]
SHORT_CASES = [
    (BaseExperiment, dict(exp_name="t", duration=0.05, n_trials=5)),
    (BlockExperiment, dict(exp_name="t", block_duration=0.05, block_trial_size=5, n_blocks=2)),
]
IDS = ["BaseExperiment", "BlockExperiment"]
FAILURES = [RuntimeError("stimulus failed mid-run"), KeyboardInterrupt()]
FAILURE_IDS = ["RuntimeError", "KeyboardInterrupt"]


@pytest.mark.parametrize("base, kwargs", CASES, ids=IDS)
@pytest.mark.parametrize("fail", FAILURES, ids=FAILURE_IDS)
def test_run_stops_the_recording_when_the_trial_loop_raises(tmp_path, base, kwargs, fail):
    exp, eeg, state = _experiment(base, fail, str(tmp_path / "recording.csv"), **kwargs)
    with pytest.raises(type(fail)):
        exp.run(instructions=False)
    assert eeg.started
    assert eeg.stopped
    assert state.closed


@pytest.mark.parametrize("base, kwargs", CASES, ids=IDS)
@pytest.mark.parametrize("fail", FAILURES, ids=FAILURE_IDS)
def test_run_saves_the_vr_timing_when_the_trial_loop_raises(tmp_path, base, kwargs, fail):
    save_fn = str(tmp_path / "recording.csv")
    exp, eeg, state = _experiment(base, fail, save_fn, use_vr=True, **kwargs)
    with pytest.raises(type(fail)):
        exp.run(instructions=False)
    assert eeg.stopped
    assert state.timing == save_fn
    assert state.closed


@pytest.mark.parametrize("use_vr", [False, True], ids=["monitor", "vr"])
@pytest.mark.parametrize("base, kwargs", SHORT_CASES, ids=IDS)
def test_session_file_says_completed_when_the_trial_loop_ran_to_its_end(tmp_path, base, kwargs,
                                                                         use_vr):
    exp, eeg, state = _experiment(base, None, str(tmp_path / "recording.csv"), use_vr=use_vr,
                                  **kwargs)
    exp.run(instructions=False)
    session = _session(tmp_path)
    assert session["completed"] is True
    assert session["reason"] is None
    assert state.closed


@pytest.mark.parametrize("use_vr", [False, True], ids=["monitor", "vr"])
@pytest.mark.parametrize("base, kwargs", CASES, ids=IDS)
def test_session_file_records_the_exception_that_ended_the_run(tmp_path, base, kwargs, use_vr):
    exp, eeg, state = _experiment(base, RuntimeError("stimulus failed mid-run"),
                                  str(tmp_path / "recording.csv"), use_vr=use_vr, **kwargs)
    with pytest.raises(RuntimeError, match="stimulus failed mid-run"):
        exp.run(instructions=False)
    session = _session(tmp_path)
    assert session["completed"] is False
    assert session["reason"] == "RuntimeError: stimulus failed mid-run"


@pytest.mark.parametrize("use_vr", [False, True], ids=["monitor", "vr"])
@pytest.mark.parametrize("base, kwargs", CASES, ids=IDS)
def test_session_file_says_aborted_by_user_after_a_keyboard_interrupt(tmp_path, base, kwargs,
                                                                     use_vr):
    exp, eeg, state = _experiment(base, KeyboardInterrupt(), str(tmp_path / "recording.csv"),
                                  use_vr=use_vr, **kwargs)
    with pytest.raises(KeyboardInterrupt):
        exp.run(instructions=False)
    session = _session(tmp_path)
    assert session["completed"] is False
    assert session["reason"] == "Aborted by user"
    assert ("vr" in session) is use_vr


@pytest.mark.parametrize("use_vr", [False, True], ids=["monitor", "vr"])
@pytest.mark.parametrize("base, kwargs", CASES, ids=IDS)
def test_session_file_says_aborted_by_user_after_the_cancel_key(tmp_path, base, kwargs, use_vr):
    exp, eeg, state = _experiment(base, None, str(tmp_path / "recording.csv"), use_vr=use_vr,
                                  cancel_after=2, **kwargs)
    exp.run(instructions=False)
    session = _session(tmp_path)
    assert session["completed"] is False
    assert session["reason"] == "Aborted by user"
    assert state.closed


def test_session_file_says_aborted_by_user_after_cancelling_a_block_screen(tmp_path):
    exp, eeg, state = _experiment(BlockExperiment, None, str(tmp_path / "recording.csv"),
                                  cancel_block=True, **CASES[1][1])
    exp.run(instructions=False)
    assert _session(tmp_path) == {"completed": False, "reason": "Aborted by user"}
    assert state.draws == 0


@pytest.mark.parametrize("base, kwargs", SHORT_CASES, ids=IDS)
def test_monitor_session_file_has_no_vr_section(tmp_path, base, kwargs):
    exp, eeg, state = _experiment(base, None, str(tmp_path / "recording.csv"), **kwargs)
    exp.run(instructions=False)
    assert _session(tmp_path) == {"completed": True, "reason": None}


def test_vr_session_file_holds_the_window_summary_as_plain_json(tmp_path):
    exp, eeg, state = _experiment(BaseExperiment, None, str(tmp_path / "recording.csv"),
                                  use_vr=True, **SHORT_CASES[0][1])
    exp.run(instructions=False)
    text = (tmp_path / "recording_session.json").read_text(encoding="utf-8")
    assert text.startswith('{\n  "completed": true,\n  "reason": null,\n  "vr": {\n')
    assert _session(tmp_path)["vr"] == {
        "backend": "openxr", "stimulus_distance_m": 1.0, "missed_vsyncs": 3,
        "runtime_to_wallclock_offset_s": 1.5e9, "longest_step_ms": None,
        "eye_size_px": [1616, 1648], "manifest": "oculus.json"}


@pytest.mark.parametrize("base, kwargs", CASES, ids=IDS)
def test_a_failed_session_summary_does_not_hide_the_original_exception(tmp_path, caplog, base,
                                                                       kwargs):
    save_fn = str(tmp_path / "recording.csv")
    exp, eeg, state = _experiment(base, RuntimeError("stimulus failed mid-run"), save_fn,
                                  use_vr=True, summary=ValueError("summary failed"), **kwargs)
    with pytest.raises(RuntimeError, match="stimulus failed mid-run"):
        exp.run(instructions=False)
    assert eeg.stopped
    assert state.timing == save_fn
    assert state.closed
    assert not (tmp_path / "recording_session.json").exists()
    assert "Could not write the session file" in caplog.text
    assert "summary failed" in caplog.text


@pytest.mark.parametrize("fail, kwargs", [(None, SHORT_CASES[0][1]),
                                           (RuntimeError("stimulus failed mid-run"), CASES[0][1])],
                         ids=["completed", "RuntimeError"])
def test_an_unwritable_session_file_does_not_stop_the_cleanup(tmp_path, caplog, fail, kwargs):
    save_fn = str(tmp_path / "missing" / "recording.csv")
    exp, eeg, state = _experiment(BaseExperiment, fail, save_fn, **kwargs)
    if fail is None:
        exp.run(instructions=False)
    else:
        with pytest.raises(RuntimeError, match="stimulus failed mid-run"):
            exp.run(instructions=False)
    assert eeg.stopped
    assert state.closed
    assert "Could not write the session file" in caplog.text


def test_no_session_file_without_a_save_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    exp, eeg, state = _experiment(BaseExperiment, None, None, **SHORT_CASES[0][1])
    exp.run(instructions=False)
    assert list(tmp_path.iterdir()) == []
    assert state.closed


@pytest.mark.parametrize("use_vr", [False, True], ids=["monitor", "vr"])
@pytest.mark.parametrize("base, kwargs", SHORT_CASES, ids=IDS)
def test_only_headset_runs_check_the_eye_separation(tmp_path, base, kwargs, use_vr):
    exp, eeg, state = _experiment(base, None, str(tmp_path / "recording.csv"), use_vr=use_vr,
                                  **kwargs)
    exp.run(instructions=False)
    assert (state.eye_checks > 0) is use_vr


CHANGED_MESSAGE = ("RuntimeError: Eye separation changed from 68.2 mm to 63.1 mm during the run, "
                   "so the stimulus is no longer at the stated distance; restart the session.")
HEADSET_CASES = [
    (BaseExperiment, dict(exp_name="t", duration=0.3, n_trials=5)),
    (BlockExperiment, dict(exp_name="t", block_duration=0.1, block_trial_size=5, n_blocks=3)),
]
LONG_HEADSET_CASES = [
    (BaseExperiment, dict(exp_name="t", duration=2, n_trials=5)),
    (BlockExperiment, dict(exp_name="t", block_duration=2, block_trial_size=5, n_blocks=3)),
]


def _headset_experiment(base, save_fn, on_trial=None, on_block=None, **kwargs):
    win = _bare(_views_apart(63.2))
    log = SimpleNamespace(trials=[], blocks=[], locked_at_setup="unset")

    class _Experiment(base):
        def load_stimulus(self):
            pass

        def present_stimulus(self, idx):
            log.trials.append(getattr(self, "current_block_index", 0))
            if on_trial is not None:
                on_trial(win, len(log.trials))

        def present_iti(self):
            pass

        def setup(self, instructions=True):
            self.window = SimpleNamespace(close=lambda: None)
            self.vr = win
            win._views = _views_apart(68.2)
            log.locked_at_setup = win._locked_eye_separation_mm
            return True

        def _draw(self, present_stimulus):
            present_stimulus()

        def _clear_user_input(self):
            pass

        def _user_input(self, input_type):
            return False

        def _show_block_instructions(self, block_index):
            log.blocks.append(block_index)
            if on_block is not None:
                on_block(win, block_index)
            return True

    exp = _Experiment(eeg=_Recorder(), save_fn=save_fn, iti=0.0, soa=0.01, jitter=0.0, **kwargs)
    exp.use_vr = True
    return exp, win, log


@pytest.mark.parametrize("base, kwargs", HEADSET_CASES, ids=IDS)
def test_headset_run_locks_the_eye_separation_at_its_first_trial(tmp_path, base, kwargs):
    exp, win, log = _headset_experiment(base, str(tmp_path / "recording.csv"), **kwargs)
    exp.run(instructions=False)
    assert log.locked_at_setup is None
    assert win._locked_eye_separation_mm == pytest.approx(68.2)
    session = _session(tmp_path)
    assert session["completed"] is True
    assert session["vr"]["eye_separation_mm"] == 68.2


@pytest.mark.parametrize("base, kwargs", HEADSET_CASES, ids=IDS)
def test_an_unchanged_eye_separation_never_ends_the_run(tmp_path, base, kwargs):
    exp, win, log = _headset_experiment(base, str(tmp_path / "recording.csv"), **kwargs)
    exp.run(instructions=False)
    assert len(log.trials) >= 10
    assert set(log.trials) == set(range(kwargs.get("n_blocks", 1)))
    assert _session(tmp_path)["completed"] is True


def _move_after_trial(separation_mm, trial):
    def on_trial(win, presented):
        if presented == trial:
            win._views = _views_apart(separation_mm)
    return on_trial


@pytest.mark.parametrize("base, kwargs", LONG_HEADSET_CASES, ids=IDS)
def test_an_eye_separation_change_over_1_mm_ends_the_run_before_the_next_trial(tmp_path, base,
                                                                             kwargs):
    exp, win, log = _headset_experiment(base, str(tmp_path / "recording.csv"),
                                        on_trial=_move_after_trial(63.1, 3), **kwargs)
    with pytest.raises(RuntimeError, match="Eye separation changed"):
        exp.run(instructions=False)
    assert len(log.trials) == 3
    session = _session(tmp_path)
    assert session["completed"] is False
    assert session["reason"] == CHANGED_MESSAGE
    assert session["vr"]["eye_separation_mm"] == 68.2


@pytest.mark.parametrize("base, kwargs", HEADSET_CASES, ids=IDS)
def test_an_eye_separation_change_under_1_mm_does_not_end_the_run(tmp_path, base, kwargs):
    exp, win, log = _headset_experiment(base, str(tmp_path / "recording.csv"),
                                        on_trial=_move_after_trial(69.1, 3), **kwargs)
    exp.run(instructions=False)
    assert len(log.trials) > 3
    assert _session(tmp_path)["completed"] is True


def test_a_change_on_a_later_block_screen_ends_the_run_at_that_blocks_first_trial(tmp_path):
    def on_block(win, block_index):
        if block_index == 1:
            win._views = _views_apart(63.1)

    exp, win, log = _headset_experiment(BlockExperiment, str(tmp_path / "recording.csv"),
                                        on_block=on_block, **LONG_HEADSET_CASES[1][1])
    with pytest.raises(RuntimeError, match="Eye separation changed"):
        exp.run(instructions=False)
    assert log.blocks == [0, 1]
    assert set(log.trials) == {0}
    assert _session(tmp_path)["reason"] == CHANGED_MESSAGE


def test_the_eye_separation_is_locked_once_per_run_not_once_per_block(tmp_path):
    def on_block(win, block_index):
        win._views = _views_apart({0: 68.2, 1: 68.9, 2: 69.5}[block_index])

    exp, win, log = _headset_experiment(BlockExperiment, str(tmp_path / "recording.csv"),
                                        on_block=on_block, **HEADSET_CASES[1][1])
    with pytest.raises(RuntimeError, match="from 68.2 mm to 69.5 mm during the run"):
        exp.run(instructions=False)
    assert set(log.trials) == {0, 1}


@pytest.mark.parametrize("base, kwargs", LONG_HEADSET_CASES, ids=IDS)
def test_eye_separation_is_written_when_the_run_ended_by_an_exception(tmp_path, base, kwargs):
    def session_stops(win, presented):
        if presented == 3:
            win._views = None
            raise RuntimeError("OpenXR session stopped mid-run (state STOPPING)")

    exp, win, log = _headset_experiment(base, str(tmp_path / "recording.csv"),
                                        on_trial=session_stops, **kwargs)
    with pytest.raises(RuntimeError, match="stopped mid-run"):
        exp.run(instructions=False)
    session = _session(tmp_path)
    assert session["completed"] is False
    assert session["reason"] == "RuntimeError: OpenXR session stopped mid-run (state STOPPING)"
    assert session["vr"]["eye_separation_mm"] == 68.2
