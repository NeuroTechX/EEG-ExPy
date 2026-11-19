"""Per-eye text and stimuli land where each eye needs them, whatever their units."""

from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("psychopy")

from eegnb.devices.vr import VR
from eegnb.experiments.Experiment import BaseExperiment
from eegnb.experiments.visual_vep import pattern_reversal_vep
from eegnb.experiments.visual_vep.pattern_reversal_vep import VisualPatternReversalVEP


class _Experiment(BaseExperiment):
    def load_stimulus(self):
        pass

    def present_stimulus(self, idx):
        pass


def _experiment(size=(1616, 1648)):
    exp = _Experiment.__new__(_Experiment)
    exp.window = SimpleNamespace(size=size)
    return exp


def test_pixel_text_is_shifted_by_half_the_eye_buffer_width():
    assert _experiment()._eye_axis_pos(0.1, 'pix') == pytest.approx((80.8, 0))


def test_norm_text_takes_the_offset_unchanged():
    assert _experiment()._eye_axis_pos(-0.1, 'norm') == (-0.1, 0)


def test_height_text_is_scaled_by_the_aspect_ratio():
    x, y = _experiment((1600, 800))._eye_axis_pos(0.5, 'height')
    assert (x, y) == pytest.approx((0.5, 0))


def _pattern_reversal(monkeypatch):
    def stim(*args, **kwargs):
        return SimpleNamespace(**kwargs)

    monkeypatch.setattr(pattern_reversal_vep, 'visual', SimpleNamespace(
        Rect=stim, ImageStim=stim, GratingStim=stim, TextStim=stim))
    monkeypatch.setattr(VisualPatternReversalVEP, 'create_vr_checkerboard',
                        staticmethod(lambda checks: {'img': None}))
    exp = VisualPatternReversalVEP.__new__(VisualPatternReversalVEP)
    exp.use_vr = True
    exp.soa = 0.5
    exp.display_refresh_rate = 120
    exp.window = SimpleNamespace(displayRefreshRate=120, size=np.array([1600, 1600]))
    exp.vr = SimpleNamespace(stimulus_distance_m=2.0, asked=[])
    exp.vr.offsets_at_distance = lambda d: exp.vr.asked.append(d) or (0.15, -0.15)
    return exp


def test_pattern_reversal_places_each_eyes_stimulus_at_the_windows_distance(monkeypatch):
    exp = _pattern_reversal(monkeypatch)
    stim = exp.load_stimulus()
    assert set(exp.vr.asked) == {2.0}
    for eye, x in (('left', 0.15), ('right', -0.15)):
        assert [c.pos for c in stim[eye]['checkerboards']] == [(x * 800, 0)] * 2
        assert stim[eye]['fixation'].pos == [x, 0]
        assert stim[eye]['vr_block_instructions'].pos == (x, 0)


@pytest.mark.parametrize('distance_m', [None, 0, float('inf')])
def test_pattern_reversal_refuses_a_distance_that_is_not_positive_and_finite(monkeypatch,
                                                                             distance_m):
    exp = _pattern_reversal(monkeypatch)
    exp.vr = VR.__new__(VR)
    exp.vr._closed = True
    exp.stimulus_distance_m = distance_m
    with pytest.raises(ValueError, match='positive, finite'):
        exp.setup(instructions=False)
