"""VR controller input over OpenXR actions, against a fake ``xr`` module."""

import enum
import logging
import time
from types import SimpleNamespace

import pytest

pytest.importorskip("psychopy")

from eegnb.devices.vr import VR, TOUCH_PROFILE, XBOX_PROFILE
from eegnb.experiments.Experiment import BaseExperiment

LEFT, RIGHT, PAD = '/user/hand/left', '/user/hand/right', '/user/gamepad'


class _SessionState(enum.Enum):
    IDLE = 1
    READY = 2
    SYNCHRONIZED = 3
    VISIBLE = 4
    FOCUSED = 5


class _SessionNotFocused(Exception):
    pass


class _FakeXR:
    ActionType = SimpleNamespace(FLOAT_INPUT='float', BOOLEAN_INPUT='bool')
    SessionState = _SessionState
    SessionNotFocused = _SessionNotFocused

    def __init__(self, reject=()):
        self.reject = set(reject)
        self.suggested = {}
        self.actions = []
        self.syncs = 0
        self.bools = {}
        self.floats = {}
        self.inactive = False

    def ActionCreateInfo(self, **kw):
        return SimpleNamespace(**kw)

    def ActionSuggestedBinding(self, action, binding):
        return (action.name, binding)

    def InteractionProfileSuggestedBinding(self, **kw):
        return SimpleNamespace(**kw)

    def ActionsSyncInfo(self, **kw):
        return SimpleNamespace(**kw)

    def ActiveActionSet(self, action_set, subaction_path):
        return (action_set, subaction_path)

    def ActionStateGetInfo(self, action, subaction_path):
        return SimpleNamespace(action=action, subaction_path=subaction_path)

    def string_to_path(self, instance, text):
        return text

    def create_action(self, action_set, create_info):
        action = SimpleNamespace(name=create_info.action_name, kind=create_info.action_type)
        self.actions.append(action)
        return action

    def suggest_interaction_profile_bindings(self, instance, suggested_bindings):
        profile = suggested_bindings.interaction_profile
        if profile in self.reject:
            raise RuntimeError("XR_ERROR_PATH_UNSUPPORTED")
        self.suggested[profile] = list(suggested_bindings.suggested_bindings)

    def sync_actions(self, session, sync_info):
        self.syncs += 1

    def get_action_state_boolean(self, session, get_info):
        key = (get_info.action.name, get_info.subaction_path)
        return SimpleNamespace(current_state=self.bools.get(key, False),
                               is_active=not self.inactive)

    def get_action_state_float(self, session, get_info):
        key = (get_info.action.name, get_info.subaction_path)
        return SimpleNamespace(current_state=self.floats.get(key, 0.0),
                               is_active=not self.inactive)


def _window(reject=()):
    win = VR.__new__(VR)
    win._xr = _FakeXR(reject)
    win.instance = win.session = 'handle'
    win._action_set = 'set'
    win._session_running = True
    win._session_state = _SessionState.FOCUSED
    win._closed = True
    win._input_enabled = False
    win._actions = {}
    win._input_paths = {}
    win._buttons = {}
    win._prev_buttons = {}
    win._triggers = {}
    win._input_poll_time_s = 0.0
    win._setup_input()
    return win


def _press(win, **states):
    xr = win._xr
    xr.bools = {}
    xr.floats = {}
    for key, value in states.items():
        name, _, where = key.partition('__')
        path = {'left': LEFT, 'right': RIGHT, 'pad': PAD}.get(where, 0)
        table = xr.floats if name.startswith(('trigger', 'xbox')) else xr.bools
        table[(name, path)] = value
    win._poll_input()


def test_setup_binds_touch_and_xbox_profiles_per_the_spec_paths():
    win = _window()
    suggested = win._xr.suggested
    assert set(suggested) == {TOUCH_PROFILE, XBOX_PROFILE}
    touch = dict((b, a) for a, b in suggested[TOUCH_PROFILE])
    assert touch[f'{LEFT}/input/trigger/value'] == 'trigger'
    assert touch[f'{RIGHT}/input/trigger/value'] == 'trigger'
    assert touch[f'{RIGHT}/input/a/click'] == 'button_a'
    assert touch[f'{RIGHT}/input/b/click'] == 'button_b'
    assert touch[f'{LEFT}/input/x/click'] == 'button_x'
    assert touch[f'{LEFT}/input/y/click'] == 'button_y'
    xbox = dict((b, a) for a, b in suggested[XBOX_PROFILE])
    assert xbox[f'{PAD}/input/trigger_left/value'] == 'xbox_trigger_left'
    assert xbox[f'{PAD}/input/trigger_right/value'] == 'xbox_trigger_right'
    assert xbox[f'{PAD}/input/y/click'] == 'button_y'
    assert win._input_enabled


def test_index_trigger_values_per_controller():
    win = _window()
    _press(win, trigger__left=0.25, trigger__right=0.75,
           xbox_trigger_left=0.5, xbox_trigger_right=0.125)
    assert win.getIndexTriggerValues('LeftTouch') == (0.25, 0.0)
    assert win.getIndexTriggerValues('RightTouch') == (0.0, 0.75)
    assert win.getIndexTriggerValues('Touch') == (0.25, 0.75)
    assert win.getIndexTriggerValues('Xbox') == (0.5, 0.125)
    assert win.getIndexTriggerValues() == (0.5, 0.125)
    assert win.getIndexTriggerValues('Touch', deadzone=True) == (0.0, 0.75)
    assert win.getIndexTriggerValues('Remote') == (0.0, 0.0)


def test_released_is_a_falling_edge_between_two_synced_frames():
    win = _window()
    _press(win, button_a__right=True)
    assert win.getButtons(['A'], 'RightTouch', 'released')[0] is False
    assert win.getButtons(['A'], 'RightTouch', 'pressed')[0] is True
    assert win.getButtons(['A'], 'RightTouch', 'continuous')[0] is True
    _press(win, button_a__right=False)
    assert win.getButtons(['A'], 'RightTouch', 'released')[0] is True
    assert win.getButtons(['A'], 'RightTouch', 'pressed')[0] is False
    assert win.getButtons(['A'], 'RightTouch', 'continuous')[0] is False
    _press(win, button_a__right=False)
    assert win.getButtons(['A'], 'RightTouch', 'released')[0] is False


def test_buttons_live_on_their_own_hand_and_on_the_gamepad():
    win = _window()
    _press(win, button_a__right=True, button_x__left=True, button_b__pad=True)
    assert win.getButtons('A', 'RightTouch')[0]
    assert not win.getButtons('A', 'LeftTouch')[0]
    assert win.getButtons('X', 'LeftTouch')[0]
    assert not win.getButtons('X', 'RightTouch')[0]
    assert win.getButtons(['A', 'X'], 'Touch')[0]
    assert not win.getButtons(['A', 'B'], 'Touch')[0]
    assert win.getButtons(['B'], 'Xbox')[0]
    assert not win.getButtons(['A'], 'Xbox')[0]
    assert win.getButtons(['Home'], 'Xbox') == (False, win._input_poll_time_s)


def test_button_timestamp_is_the_poll_time_on_the_perf_counter_clock():
    win = _window()
    before = time.perf_counter()
    _press(win, button_y__left=True)
    after = time.perf_counter()
    tsec = win.getButtons(['Y'], 'LeftTouch')[1]
    assert before <= tsec <= after


def test_unknown_names_and_states_raise_like_rift():
    win = _window()
    with pytest.raises(KeyError):
        win.getIndexTriggerValues('Wiimote')
    with pytest.raises(KeyError):
        win.getButtons(['A'], 'Wiimote')
    with pytest.raises(KeyError):
        win.getButtons(['Z'], 'Xbox')
    with pytest.raises(ValueError):
        win.getButtons(['A'], 'Xbox', 'sideways')
    with pytest.raises(ValueError):
        win.getButtons(3, 'Xbox')
    with pytest.raises(TypeError):
        win.updateInputState('Xbox')


def test_inactive_actions_read_as_released_and_zero():
    win = _window()
    _press(win, button_a__right=True, trigger__right=1.0)
    win._xr.inactive = True
    win._poll_input()
    assert win.getButtons('A', 'RightTouch')[0] is False
    assert win.getIndexTriggerValues('RightTouch') == (0.0, 0.0)


def test_one_profile_rejected_keeps_the_other_and_warns(caplog):
    with caplog.at_level(logging.WARNING):
        win = _window(reject=[XBOX_PROFILE])
    assert win._input_enabled
    assert set(win._xr.suggested) == {TOUCH_PROFILE}
    assert XBOX_PROFILE in caplog.text


def test_all_bindings_rejected_falls_back_to_keyboard_only(caplog):
    with caplog.at_level(logging.WARNING):
        win = _window(reject=[TOUCH_PROFILE, XBOX_PROFILE])
    assert not win._input_enabled
    assert "keyboard only" in caplog.text
    win.updateInputState()
    assert win._xr.syncs == 0
    assert win.getIndexTriggerValues('LeftTouch') == (0.0, 0.0)
    assert win.getButtons(['A'], 'RightTouch', 'released')[0] is False


def test_action_creation_failure_falls_back_to_keyboard_only(caplog):
    win = VR.__new__(VR)
    win._closed = True
    win._xr = _FakeXR()
    win._xr.create_action = lambda **kw: (_ for _ in ()).throw(RuntimeError("boom"))
    win.instance = 'handle'
    win._action_set = 'set'
    win._input_enabled = True
    with caplog.at_level(logging.WARNING):
        win._setup_input()
    assert not win._input_enabled
    assert "keyboard only" in caplog.text


def test_no_sync_while_the_session_is_not_running():
    win = _window()
    win._session_running = False
    win._poll_input()
    assert win._xr.syncs == 0
    win._session_running = True
    win._poll_input()
    assert win._xr.syncs == 1


def test_sync_failure_disables_input_instead_of_raising(caplog):
    win = _window()

    def fail(session, info):
        raise RuntimeError("session lost")

    win._xr.sync_actions = fail
    with caplog.at_level(logging.WARNING):
        win.updateInputState()
    assert not win._input_enabled
    assert "poll failed" in caplog.text


def test_unfocused_session_keeps_input_enabled_and_reads_once_focused(caplog):
    win = _window()
    win._session_state = _SessionState.READY
    with caplog.at_level(logging.WARNING):
        _press(win, button_a__right=True)
    assert win._input_enabled
    assert win._xr.syncs == 0
    assert "poll failed" not in caplog.text
    assert win.getButtons('A', 'RightTouch')[0] is False
    win._session_state = _SessionState.FOCUSED
    _press(win, button_a__right=True)
    assert win._xr.syncs == 1
    assert win.getButtons('A', 'RightTouch')[0] is True


def test_losing_focus_clears_held_input_without_a_released_edge():
    win = _window()
    _press(win, button_a__right=True, trigger__right=1.0)
    win._session_state = _SessionState.VISIBLE
    win._poll_input()
    assert win._input_enabled
    assert win.getButtons('A', 'RightTouch')[0] is False
    assert win.getIndexTriggerValues('RightTouch') == (0.0, 0.0)
    win._session_state = _SessionState.FOCUSED
    _press(win, button_a__right=False)
    assert win.getButtons('A', 'RightTouch', 'released')[0] is False


def test_session_not_focused_from_sync_clears_state_and_keeps_input_enabled(caplog):
    win = _window()
    _press(win, button_a__right=True, trigger__right=1.0)

    def lose_focus(session, info):
        raise _SessionNotFocused()

    win._xr.sync_actions = lose_focus
    with caplog.at_level(logging.WARNING):
        win.updateInputState()
    assert win._input_enabled
    assert "poll failed" not in caplog.text
    assert win.getButtons('A', 'RightTouch')[0] is False
    assert win.getButtons('A', 'RightTouch', 'released')[0] is False
    assert win.getIndexTriggerValues('RightTouch') == (0.0, 0.0)
    del win._xr.sync_actions
    _press(win, button_a__right=True)
    assert win.getButtons('A', 'RightTouch')[0] is True


def test_update_input_state_polls_and_validates_names():
    win = _window()
    win.updateInputState(['Xbox', 'LeftTouch'])
    assert win._xr.syncs == 1
    with pytest.raises(KeyError):
        win.updateInputState(['Wiimote'])


def test_experiment_get_vr_input_reads_trigger_and_released_button():
    win = _window()
    exp = SimpleNamespace(vr=win)
    get = BaseExperiment.get_vr_input

    _press(win)
    assert get(exp, 'RightTouch', trigger=True) is False
    assert get(exp, 'RightTouch', button='A') is False

    _press(win, trigger__right=0.9)
    assert get(exp, 'RightTouch', trigger=True) is True
    assert get(exp, 'LeftTouch', trigger=True) is False

    _press(win, button_a__right=True)
    assert get(exp, 'RightTouch', button='A') is False
    _press(win, button_a__right=False)
    assert get(exp, 'RightTouch', button='A') is True

    _press(win, xbox_trigger_right=0.3)
    assert get(exp, 'Xbox', trigger=True) is True


def test_experiment_clear_vr_input_polls_the_window():
    win = _window()
    BaseExperiment.clear_vr_input(SimpleNamespace(use_vr=True, vr=win))
    assert win._xr.syncs == 1
    BaseExperiment.clear_vr_input(SimpleNamespace(use_vr=False, vr=win))
    assert win._xr.syncs == 1
