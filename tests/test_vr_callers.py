import pandas as pd
import pytest
from unittest.mock import MagicMock

pytest.importorskip("psychopy")

from eegnb.experiments.Experiment import BaseExperiment
from eegnb.experiments.visual_ssvep.ssvep import VisualSSVEP


class _HeadLockedWindow:
    def __init__(self):
        self.default_view_calls = 0
        self.flips = 0

    def setDefaultView(self):
        self.default_view_calls += 1

    def flip(self):
        self.flips += 1


def test_draw_in_vr_sets_default_view_without_head_pose_calls():
    exp = object.__new__(VisualSSVEP)
    exp.use_vr = True
    exp.window = _HeadLockedWindow()
    present = MagicMock()
    BaseExperiment._draw(exp, present)
    assert exp.window.default_view_calls == 1
    present.assert_called_once_with()


def test_ssvep_present_stimulus_in_vr_sets_default_view_each_frame():
    exp = object.__new__(VisualSSVEP)
    exp.use_vr = True
    exp.eeg = None
    exp.window = _HeadLockedWindow()
    exp.trials = pd.DataFrame({"parameter": [0]})
    exp.markernames = [1]
    exp.stim_patterns = [{"n_cycles": 2, "cycle": (3, 2)}]
    exp.grating = MagicMock()
    exp.grating_neg = MagicMock()
    exp.fixation = MagicMock()
    exp.present_stimulus(0)
    assert exp.window.default_view_calls == 10
    assert exp.window.flips == 10
