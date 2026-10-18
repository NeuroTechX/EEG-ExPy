"""Headset passthrough behind instruction screens, against a fake ``xr`` module."""

import ctypes
import math
from types import SimpleNamespace

import pytest

pytest.importorskip("psychopy")

from eegnb.devices import vr as vr_module
from eegnb.devices.vr import VR
from eegnb.experiments.Experiment import BaseExperiment

PASSTHROUGH_EXT = 'XR_FB_passthrough'
ALPHA_BIT = 0x2


class _Layer(ctypes.Structure):
    _fields_ = [('layer_flags', ctypes.c_uint64)]


class _FakeXR:
    FB_PASSTHROUGH_EXTENSION_NAME = PASSTHROUGH_EXT
    PassthroughFlagsFB = SimpleNamespace(NONE=0)
    PassthroughLayerPurposeFB = SimpleNamespace(RECONSTRUCTION=0)
    CompositionLayerFlags = SimpleNamespace(BLEND_TEXTURE_SOURCE_ALPHA_BIT=ALPHA_BIT)
    EnvironmentBlendMode = SimpleNamespace(OPAQUE=1)

    def __init__(self, fail_start=False):
        self.calls = []
        self.fail_start = fail_start
        self.frames = []

    def PassthroughCreateInfoFB(self, **kw):
        return SimpleNamespace(**kw)

    def PassthroughLayerCreateInfoFB(self, **kw):
        return SimpleNamespace(**kw)

    def CompositionLayerPassthroughFB(self, layer_handle):
        return _Layer(0)

    def create_passthrough_fb(self, session, info):
        self.calls.append('create')
        return 'passthrough'

    def create_passthrough_layer_fb(self, session, info):
        self.calls.append('create_layer')
        return 'layer'

    def passthrough_start_fb(self, handle):
        if self.fail_start:
            raise RuntimeError('passthrough over Link is off')
        self.calls.append('start')

    def passthrough_layer_resume_fb(self, handle):
        self.calls.append('resume')

    def passthrough_layer_pause_fb(self, handle):
        self.calls.append('pause_layer')

    def passthrough_pause_fb(self, handle):
        self.calls.append('pause')

    def SwapchainImageReleaseInfo(self):
        return None

    def release_swapchain_image(self, **kw):
        pass

    def FrameEndInfo(self, **kw):
        return SimpleNamespace(**kw)

    def end_frame(self, session, frame_end_info):
        self.frames.append(frame_end_info)


def _bare(fake, extensions=(PASSTHROUGH_EXT,)):
    win = VR.__new__(VR)
    win._xr = fake
    win._extensions = set(extensions)
    win.session = 'session'
    win._passthrough = None
    win._passthrough_layer = None
    win._passthrough_composition = None
    win._passthrough_on = False
    win._closed = True
    return win


def test_without_the_extension_passthrough_stays_off():
    fake = _FakeXR()
    win = _bare(fake, extensions=())
    assert win.set_passthrough(True) is False
    assert win.passthrough_on is False and fake.calls == []


def test_passthrough_is_created_once_then_paused_and_resumed():
    fake = _FakeXR()
    win = _bare(fake)
    assert win.set_passthrough(True) is True
    assert win.set_passthrough(False) is False
    assert win.set_passthrough(True) is True
    assert fake.calls == ['create', 'create_layer', 'start', 'resume',
                          'pause_layer', 'pause', 'start', 'resume']


def test_a_runtime_that_refuses_passthrough_leaves_the_frame_opaque():
    win = _bare(_FakeXR(fail_start=True))
    assert win.set_passthrough(True) is False
    assert win.passthrough_on is False


def _submit(win, monkeypatch):
    monkeypatch.setattr(vr_module, 'GL', SimpleNamespace(
        glBindFramebuffer=lambda *a: None, GL_FRAMEBUFFER=0))
    win._frame_state = SimpleNamespace(should_render=True, predicted_display_time=1,
                                       predicted_display_period=8333333)
    win._views = [object(), object()]
    win._monoscopic = False
    win._acquired = {0: 10, 1: 11}
    win._swapchains = ['left', 'right']
    win._layer = _Layer(0)
    win.mirror_swap_every = 0
    win._mirror_swap_counter = 0
    win._frame_step_ns = None
    win._xr_time_to_s = lambda t: 0.0
    win._submit_frame()
    return win._xr.frames[-1].layers


def test_passthrough_layer_goes_under_an_alpha_blended_projection(monkeypatch):
    fake = _FakeXR()
    win = _bare(fake)
    win.set_passthrough(True)
    layers = _submit(win, monkeypatch)
    assert [ref._obj for ref in layers] == [win._passthrough_composition, win._layer]
    assert win._layer.layer_flags == ALPHA_BIT


def test_without_passthrough_only_the_opaque_projection_is_submitted(monkeypatch):
    win = _bare(_FakeXR())
    layers = _submit(win, monkeypatch)
    assert [ref._obj for ref in layers] == [win._layer]
    assert win._layer.layer_flags == 0


class _Experiment(BaseExperiment):
    def load_stimulus(self):
        pass

    def present_stimulus(self, idx):
        pass


def _experiment(passthrough_instructions, use_vr=True):
    exp = _Experiment.__new__(_Experiment)
    exp.use_vr = use_vr
    exp.passthrough_instructions = passthrough_instructions
    exp.vr = SimpleNamespace(set_passthrough=lambda on: on, resume_after_stop=False)
    return exp


def test_instruction_passthrough_is_opt_in():
    assert _experiment(False)._instruction_screen(True) is False
    assert _experiment(True)._instruction_screen(True) is True
    assert _experiment(True, use_vr=False)._instruction_screen(True) is False


def test_only_instruction_screens_let_the_session_pause():
    exp = _experiment(False)
    exp._instruction_screen(True)
    assert exp.vr.resume_after_stop is True
    exp._instruction_screen(False)
    assert exp.vr.resume_after_stop is False


def test_passthrough_stays_on_after_an_instruction_screen_until_trials_start():
    exp = _experiment(True)
    calls = []
    exp.vr.set_passthrough = lambda on: calls.append(on) or on
    exp._instruction_screen(True)
    exp._instruction_screen(False)
    assert calls == [True]


class _Fov:
    def __init__(self, left, right):
        self.angle_left, self.angle_right = left, right
        self.angle_up, self.angle_down = 0.8377581, -0.8726646


def _viewed(x_left=-0.0316, x_right=0.0316):
    win = _bare(_FakeXR())
    win._views = [SimpleNamespace(fov=_Fov(-0.9075712, 0.7853982),
                                  pose=SimpleNamespace(position=SimpleNamespace(x=x_left))),
                  SimpleNamespace(fov=_Fov(-0.7853982, 0.9075712),
                                  pose=SimpleNamespace(position=SimpleNamespace(x=x_right)))]
    return win


def test_far_text_sits_on_the_optical_axis():
    win = _viewed()
    assert win.offsets_at_distance(1e9) == pytest.approx(win.compute_optical_axis_offsets())


def test_near_text_moves_nasally_by_half_the_eye_separation():
    win = _viewed()
    axis_left, axis_right = win.compute_optical_axis_offsets()
    near_left, near_right = win.offsets_at_distance(1.0)
    span = math.tan(0.9075712) + math.tan(0.7853982)
    assert near_left - axis_left == pytest.approx(2 * 0.0316 / span)
    assert near_right - axis_right == pytest.approx(-2 * 0.0316 / span)


def test_text_follows_the_distance_only_while_passthrough_shows_the_room():
    exp = _experiment(True)
    exp.left_eye_x_pos, exp.right_eye_x_pos = 0.12, -0.12
    exp.vr = SimpleNamespace(passthrough_on=False, offsets_at_distance=lambda d: (0.2, -0.2))
    assert (exp._text_x_ndc('left'), exp._text_x_ndc('right')) == (0.12, -0.12)
    exp.vr.passthrough_on = True
    assert (exp._text_x_ndc('left'), exp._text_x_ndc('right')) == (0.2, -0.2)


def test_strict_offsets_refuse_without_poses():
    win = _bare(_FakeXR())
    win._views = None
    with pytest.raises(RuntimeError, match="not located"):
        win.offsets_at_distance(1.0, strict=True)
    assert win.offsets_at_distance(1.0) == (0.0, 0.0)


def test_eye_separation_and_nasal_shift_follow_the_poses():
    win = _viewed()
    assert win.eye_separation_mm() == pytest.approx(63.2)
    left, right = win.nasal_shift_deg(1.0)
    assert left == pytest.approx(math.degrees(math.atan(0.0316)))
    assert right == pytest.approx(-left)
    bare = _bare(_FakeXR())
    bare._views = None
    assert bare.eye_separation_mm() is None


def test_stimulus_distance_sets_text_distance_with_and_without_passthrough():
    exp = _experiment(False)
    exp.left_eye_x_pos, exp.right_eye_x_pos = 0.12, -0.12
    asked = []
    exp.vr = SimpleNamespace(
        passthrough_on=False,
        offsets_at_distance=lambda d, strict=False: asked.append((d, strict)) or (0.2, -0.2))
    exp.stimulus_distance_m = 2.0
    assert (exp._text_x_ndc('left'), exp._text_x_ndc('right')) == (0.2, -0.2)
    exp.vr.passthrough_on = True
    assert (exp._text_x_ndc('left'), exp._text_x_ndc('right')) == (0.2, -0.2)
    assert {d for d, _ in asked} == {2.0} and all(strict for _, strict in asked)
    exp.stimulus_distance_m = None
    exp.vr.passthrough_on = False
    assert (exp._text_x_ndc('left'), exp._text_x_ndc('right')) == (0.12, -0.12)
