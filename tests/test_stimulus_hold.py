import itertools
import math
import random
from collections import Counter

import numpy as np
import pytest

pytest.importorskip("psychopy")

import eegnb.experiments.BlockExperiment as block_module
import eegnb.experiments.Experiment as experiment_module
from eegnb.experiments.BlockExperiment import BlockExperiment
from eegnb.experiments.Experiment import BaseExperiment
from eegnb.experiments.visual_n170.n170 import VisualN170
from eegnb.experiments.visual_p300.p300 import VisualP300
from eegnb.experiments.visual_vep.pattern_reversal_vep import VisualPatternReversalVEP

REFRESH_S = 1 / 120


class _Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        self.now += 50e-6
        return self.now


class _Window:
    def __init__(self, clock, return_delay=lambda: 0.0, stalls=None):
        self.clock = clock
        self.return_delay = return_delay
        self.stalls = stalls or {}
        self.drawn = []
        self.frames = []
        self.times = []

    def flip(self):
        self.clock.now += self.stalls.get(len(self.frames), 0.0)
        shown_at = (math.floor(self.clock.now / REFRESH_S) + 1) * REFRESH_S
        self.clock.now = shown_at + self.return_delay()
        self.frames.append(tuple(self.drawn))
        self.times.append(shown_at)
        self.drawn = []

    def setBuffer(self, eye):
        self.drawn.append(eye)

    def setDefaultView(self):
        pass

    def sync_vr_clock(self):
        pass

    def check_eye_separation(self):
        pass

    def save_timing(self, save_fn):
        pass

    def close(self):
        pass


class _Stim:
    def __init__(self, window, name):
        self.window = window
        self.name = name

    def draw(self):
        self.window.drawn.append(self.name)


class _Recorder:
    backend = "brainflow"

    def __init__(self):
        self.markers = []

    def start(self, save_fn, duration=None):
        pass

    def stop(self):
        pass

    def push_sample(self, marker, timestamp):
        self.markers.append(marker)


def _n170(window, eeg):
    exp = VisualN170(duration=3, eeg=eeg)
    exp.houses = [_Stim(window, "house")]
    exp.faces = [_Stim(window, "face")]
    return exp


def _p300(window, eeg):
    exp = VisualP300(duration=3, eeg=eeg)
    exp.nontargets = [_Stim(window, "nontarget")]
    exp.targets = [_Stim(window, "target")]
    return exp


def _pattern_reversal(window, eeg, duration=3):
    exp = VisualPatternReversalVEP(display_refresh_rate=120, eeg=eeg,
                                   block_duration_seconds=duration,
                                   block_trial_size=int(duration / 0.5) + 4, n_blocks=1)
    exp.black_background = _Stim(window, "black")
    exp.grey_background = _Stim(window, "grey")
    exp.stim = {eye: {"checkerboards": [_Stim(window, f"{eye} checks 0"),
                                        _Stim(window, f"{eye} checks 1")],
                      "fixation": _Stim(window, f"{eye} fixation")}
                for eye in ("left", "right", "monoscopic")}
    return exp


EXPERIMENTS = [_n170, _p300, _pattern_reversal]
EXPERIMENT_IDS = ["n170", "p300", "pattern_reversal"]
PATHS = pytest.mark.parametrize("use_vr", [False, True], ids=["monitor", "headset"])


def _trials(window, eeg, duration=5):
    class _Trials(BaseExperiment):
        def load_stimulus(self):
            pass

        def present_stimulus(self, idx):
            window.drawn.append(idx)
            window.flip()

        present_soa = present_stimulus

    return _Trials("trials", duration, eeg, None, n_trials=50, iti=0, soa=0.5, jitter=0)


def _drive(build, use_vr, monkeypatch, duration=None, **window_options):
    clock = _Clock()
    monkeypatch.setattr(experiment_module, "time", clock)
    window = _Window(clock, **window_options)
    eeg = _Recorder()
    exp = build(window, eeg) if duration is None else build(window, eeg, duration)
    exp.use_vr = use_vr
    exp.window = window
    if use_vr:
        exp.vr = window
    exp._clear_user_input = lambda: None
    exp._user_input = lambda input_type: False
    assert exp._run_trial_loop(clock(), exp.duration)
    return exp, window, eeg.markers


def _run(build, use_vr, monkeypatch):
    exp, window, markers = _drive(build, use_vr, monkeypatch)
    holds = [(frame, len(list(group))) for frame, group in itertools.groupby(window.frames)
             if frame]
    return exp, holds, markers


def _onsets(window):
    onsets, previous = [], None
    for frame, shown_at in zip(window.frames, window.times):
        if frame and frame != previous:
            onsets.append(shown_at)
        previous = frame
    return onsets


@PATHS
@pytest.mark.parametrize("build", EXPERIMENTS, ids=EXPERIMENT_IDS)
def test_the_stimulus_is_drawn_on_every_refresh_while_it_is_held(monkeypatch, build, use_vr):
    exp, holds, markers = _run(build, use_vr, monkeypatch)
    assert len(holds) >= 3
    for frame, refreshes in holds[:-1]:
        assert refreshes >= round(exp.soa / REFRESH_S)


@PATHS
@pytest.mark.parametrize("build", EXPERIMENTS, ids=EXPERIMENT_IDS)
def test_the_marker_is_sent_once_per_trial_not_once_per_redraw(monkeypatch, build, use_vr):
    exp, holds, markers = _run(build, use_vr, monkeypatch)
    assert len(markers) == len(holds)
    assert sum(refreshes for frame, refreshes in holds) > 10 * len(markers)


@PATHS
def test_reversals_keep_the_requested_period_without_drifting(monkeypatch, use_vr):
    delays = random.Random(3)
    exp, window, markers = _drive(_pattern_reversal, use_vr, monkeypatch, duration=30,
                                  return_delay=lambda: delays.uniform(20e-6, 400e-6))
    onsets = _onsets(window)
    assert len(onsets) == 60
    assert np.mean(np.diff(onsets[1:])) == pytest.approx(exp.soa, abs=0.25e-3)
    offsets = [onset - trial * exp.soa for trial, onset in enumerate(onsets)]
    assert max(offsets) - min(offsets) <= REFRESH_S + 1e-9


@PATHS
def test_after_a_stall_the_overdue_trials_run_at_once_and_the_schedule_resumes(monkeypatch,
                                                                              use_vr):
    exp, window, markers = _drive(_trials, use_vr, monkeypatch, stalls={100: 1.6})
    shown = [frame[0] for frame in window.frames if frame]
    order = [trial for trial, group in itertools.groupby(shown)]
    assert order == list(range(len(order)))
    refreshes = Counter(shown)
    onsets = {trial: window.times[window.frames.index((trial,))] for trial in order}
    assert refreshes[2] == refreshes[3] == 1
    assert onsets[3] - onsets[2] == pytest.approx(REFRESH_S)
    for trial in order[5:]:
        assert abs(onsets[trial] - onsets[1] - (trial - 1) * exp.soa) <= REFRESH_S + 1e-9


@PATHS
def test_a_long_block_screen_does_not_make_the_next_blocks_trials_overdue(monkeypatch, use_vr):
    clock = _Clock()
    monkeypatch.setattr(experiment_module, "time", clock)
    monkeypatch.setattr(block_module, "time", clock)
    window = _Window(clock)

    class _Blocks(BlockExperiment):
        def load_stimulus(self):
            pass

        def present_stimulus(self, idx):
            window.drawn.append((self.current_block_index, idx))
            window.flip()

        present_soa = present_stimulus

        def setup(self, instructions=True):
            return True

        def _show_block_instructions(self, block_index):
            clock.now += 5.0
            return True

    exp = _Blocks("blocks", 2, _Recorder(), None, block_trial_size=10, n_blocks=2, iti=0,
                  soa=0.5, jitter=0)
    exp.use_vr = use_vr
    exp.window = exp.vr = window
    exp._clear_user_input = lambda: None
    exp._user_input = lambda input_type: False
    exp.run(instructions=False)
    holds = [(frame[0], len(list(group))) for frame, group in itertools.groupby(window.frames)
             if frame]
    for block in (0, 1):
        refreshes = [count for (held_block, trial), count in holds if held_block == block]
        assert len(refreshes) == 4
        assert all(count >= round(exp.soa / REFRESH_S) for count in refreshes[:-1])
