"""Per-eye text lands on each eye's optical axis whatever its units."""

from types import SimpleNamespace

import pytest

pytest.importorskip("psychopy")

from eegnb.experiments.Experiment import BaseExperiment


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
