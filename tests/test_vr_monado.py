import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

if sys.platform != "linux":
    pytest.skip("the Monado-backed tests need Linux", allow_module_level=True)
if shutil.which("monado-service") is None:
    pytest.skip("monado-service is not on PATH", allow_module_level=True)
if not os.environ.get("DISPLAY"):
    pytest.skip("no DISPLAY; run under xvfb-run", allow_module_level=True)

RUNTIME_MANIFEST = next((path for path in ('/usr/share/openxr/1/openxr_monado.json',
                                           '/usr/local/share/openxr/1/openxr_monado.json')
                         if os.path.exists(path)), None)
if RUNTIME_MANIFEST is None:
    pytest.skip("no Monado OpenXR runtime manifest installed", allow_module_level=True)

xr = pytest.importorskip("xr")
pytest.importorskip("OpenGL")
pytest.importorskip("psychopy")

from eegnb.devices.vr import VR, TOUCH_PROFILE
from monado_remote import PORT, MonadoRemote

VULKAN_ICD_DIR = Path('/usr/share/vulkan/icd.d')
SERVICE_START_TIMEOUT_S = 30.0
SERVICE_STOP_TIMEOUT_S = 10.0
LOG_TAIL_LINES = 60
FOCUS_FRAME_LIMIT = 100
INPUT_FRAME_LIMIT = 20
RUN_FRAMES = 10


def _log_tail(log_path):
    lines = log_path.read_text(errors='replace').splitlines()
    return '\n'.join(lines[-LOG_TAIL_LINES:])


def _port_in_use(port):
    try:
        socket.create_connection(('127.0.0.1', port), timeout=1.0).close()
    except OSError:
        return False
    return True


def _wait_for_ipc_socket(service, socket_path, log_path):
    deadline = time.monotonic() + SERVICE_START_TIMEOUT_S
    while not socket_path.exists():
        if service.poll() is not None:
            pytest.fail(f"monado-service exited with {service.returncode} before opening "
                        f"its IPC socket\n{_log_tail(log_path)}")
        if time.monotonic() > deadline:
            pytest.fail(f"monado-service did not open {socket_path} within "
                        f"{SERVICE_START_TIMEOUT_S:.0f}s\n{_log_tail(log_path)}")
        time.sleep(0.05)


def _stop_service(service):
    service.terminate()
    try:
        service.wait(timeout=SERVICE_STOP_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        service.kill()
        service.wait()
    service.stdin.close()


def _show_log(config, log_path):
    reporter = config.pluginmanager.get_plugin('terminalreporter')
    if reporter is not None:
        reporter.write_sep('-', 'monado-service log')
        reporter.write_line(_log_tail(log_path))


@pytest.fixture(scope='module')
def monado(request, tmp_path_factory):
    if _port_in_use(PORT):
        pytest.fail(f"port {PORT} is taken; is another monado-service running?")
    runtime_dir = tmp_path_factory.mktemp('monado')
    runtime_dir.chmod(0o700)
    log_path = runtime_dir / 'monado-service.log'
    failures_before = request.session.testsfailed

    patch = pytest.MonkeyPatch()
    patch.delenv('WAYLAND_DISPLAY', raising=False)
    patch.setenv('XDG_RUNTIME_DIR', str(runtime_dir))
    patch.setenv('XR_RUNTIME_JSON', RUNTIME_MANIFEST)
    patch.setenv('XRT_COMPOSITOR_NULL', '1')
    patch.setenv('P_OVERRIDE_ACTIVE_CONFIG', 'remote')
    patch.setenv('LIBGL_ALWAYS_SOFTWARE', '1')
    lavapipe = sorted(VULKAN_ICD_DIR.glob('lvp_icd*.json'))
    if lavapipe and not {'VK_DRIVER_FILES', 'VK_ICD_FILENAMES'} & set(os.environ):
        patch.setenv('VK_DRIVER_FILES', str(lavapipe[0]))
        patch.setenv('VK_ICD_FILENAMES', str(lavapipe[0]))
    env = dict(os.environ)
    env.setdefault('XRT_LOG', 'info')

    service = None
    try:
        with log_path.open('wb') as log:
            service = subprocess.Popen(['monado-service'], stdin=subprocess.PIPE,
                                       stdout=log, stderr=subprocess.STDOUT, env=env)
        _wait_for_ipc_socket(service, runtime_dir / 'monado_comp_ipc', log_path)
        yield service
    finally:
        if service is not None:
            _stop_service(service)
        patch.undo()
        if request.session.testsfailed > failures_before:
            _show_log(request.config, log_path)


@pytest.fixture(scope='module')
def remote(monado):
    client = MonadoRemote()
    yield client
    client.close()


def _flip_until(win, done, limit=INPUT_FRAME_LIMIT):
    for _ in range(limit):
        win.flip()
        if done():
            return
    pytest.fail(f"condition not met within {limit} frames "
                f"(session {win.get_session_status()['session_state']})")


def _open_focused():
    win = VR()
    try:
        _flip_until(win, lambda: win.get_session_status()['has_input_focus'],
                    limit=FOCUS_FRAME_LIMIT)
    except BaseException:
        win.close()
        raise
    return win


@pytest.fixture(scope='class')
def win(monado):
    window = _open_focused()
    yield window
    window.close()


class TestSession:

    def test_session_reaches_focused_on_the_monado_runtime(self, win):
        status = win.get_session_status()
        assert status['session_state'] == 'FOCUSED'
        assert status['is_visible'] and status['has_input_focus']
        assert 'Monado' in win.runtime_name
        assert all(v > 0 for v in win._eye_size)

    def test_frames_run_with_an_advancing_prediction(self, win):
        first = win._frame_index
        predictions = []
        for _ in range(RUN_FRAMES):
            win.flip()
            predictions.append(win.last_predicted_display_time_s)
        assert win._frame_index == first + RUN_FRAMES
        assert None not in predictions
        assert all(later > earlier for earlier, later in zip(predictions, predictions[1:]))
        assert abs(predictions[-1] - time.perf_counter()) < 1.0
        assert 0 < win.last_display_period_ms < 1000
        assert win.displayRefreshRate > 0
        assert win.get_session_status()['session_state'] == 'FOCUSED'

    def test_telemetry_row_and_summary_carry_the_session_state(self, win):
        win.flip()
        win.log_telemetry(0, time.time(), marker=3)
        header = (['trial_idx', 'software_time', 'submitted_frame_index']
                  + list(win._DERIVED_TIMING_FIELDS))
        row = dict(zip(header, win.timing_data[-1]))
        assert row['marker'] == 3
        assert row['session_state'] == 'FOCUSED'
        assert row['submitted_frame_index'] == win._frame_index - 1
        assert row['predicted_display_time_s'] == win.last_predicted_display_time_s
        assert row['display_period_ms'] == win.last_display_period_ms
        summary = win.get_session_summary()
        assert summary['session_status']['session_state'] == 'FOCUSED'
        assert 'Monado' in summary['runtime']


def test_close_releases_the_session_and_a_new_one_can_open(monado):
    first = _open_focused()
    first.close()
    assert first.session is None
    assert first.instance is None
    second = _open_focused()
    assert second.get_session_status()['session_state'] == 'FOCUSED'
    second.close()


def _drive(remote, hand, **fields):
    controller = getattr(remote.state, hand)
    for name, value in fields.items():
        setattr(controller, name, value)
    remote.send()


def _edges(win, button, controller):
    return tuple(win.getButtons(button, controller, state)[0]
                 for state in ('continuous', 'pressed', 'released'))


def _is_idle(win):
    buttons = [win.getButtons(button, controller)[0]
               for button in 'ABXY' for controller in ('LeftTouch', 'RightTouch')]
    return not any(buttons) and win.getIndexTriggerValues('Touch') == (0.0, 0.0)


class TestInput:

    @pytest.fixture(autouse=True)
    def idle(self, win, remote):
        remote.clear()
        _flip_until(win, lambda: _is_idle(win))
        win.flip()

    def test_input_is_enabled_and_stamped_on_the_perf_counter_clock(self, win):
        assert win._input_enabled
        before = time.perf_counter()
        win.flip()
        after = time.perf_counter()
        assert before <= win.getButtons('A', 'RightTouch')[1] <= after

    @pytest.mark.parametrize('hand', ['left', 'right'])
    def test_touch_profile_is_bound_on_both_hands(self, win, hand):
        state = xr.get_current_interaction_profile(win.session, win._input_paths[hand])
        assert xr.path_to_string(win.instance, state.interaction_profile) == TOUCH_PROFILE

    def test_a_press_hold_and_release_edges_on_right_touch(self, win, remote):
        assert _edges(win, 'A', 'RightTouch') == (False, False, False)
        _drive(remote, 'right', a_click=True)
        _flip_until(win, lambda: win.getButtons('A', 'RightTouch')[0])
        assert _edges(win, 'A', 'RightTouch') == (True, True, False)
        win.flip()
        assert _edges(win, 'A', 'RightTouch') == (True, False, False)
        _drive(remote, 'right', a_click=False)
        _flip_until(win, lambda: not win.getButtons('A', 'RightTouch')[0])
        assert _edges(win, 'A', 'RightTouch') == (False, False, True)
        win.flip()
        assert _edges(win, 'A', 'RightTouch') == (False, False, False)

    def test_left_a_click_reads_as_x_on_left_touch(self, win, remote):
        _drive(remote, 'left', a_click=True)
        _flip_until(win, lambda: win.getButtons('X', 'LeftTouch')[0])
        assert _edges(win, 'X', 'LeftTouch') == (True, True, False)
        assert win.getButtons(['X'], 'Touch')[0] is True
        assert win.getButtons('X', 'RightTouch')[0] is False
        assert win.getButtons('A', 'LeftTouch')[0] is False
        assert win.getButtons('A', 'RightTouch')[0] is False

    @pytest.mark.parametrize('hand, button, controller, other',
                             [('right', 'B', 'RightTouch', 'A'),
                              ('left', 'Y', 'LeftTouch', 'X')])
    def test_b_click_reads_as_b_on_the_right_and_y_on_the_left(
            self, win, remote, hand, button, controller, other):
        _drive(remote, hand, b_click=True)
        _flip_until(win, lambda: win.getButtons(button, controller)[0])
        assert _edges(win, button, controller) == (True, True, False)
        assert win.getButtons(other, controller)[0] is False
        _drive(remote, hand, b_click=False)
        _flip_until(win, lambda: not win.getButtons(button, controller)[0])
        assert _edges(win, button, controller) == (False, False, True)

    @pytest.mark.parametrize('value, with_deadzone', [(0.2, 0.0), (0.5, 0.5)])
    def test_right_trigger_value_with_and_without_the_deadzone(
            self, win, remote, value, with_deadzone):
        _drive(remote, 'right', trigger_value=value)
        _flip_until(win, lambda: win.getIndexTriggerValues('RightTouch')[1] > 0)
        assert win.getIndexTriggerValues('RightTouch') == (0.0, pytest.approx(value, abs=1e-3))
        assert win.getIndexTriggerValues('Touch') == (0.0, pytest.approx(value, abs=1e-3))
        assert win.getIndexTriggerValues('LeftTouch') == (0.0, 0.0)
        assert win.getIndexTriggerValues('RightTouch', deadzone=True) == (
            0.0, pytest.approx(with_deadzone, abs=1e-3))

    def test_xbox_reads_idle_while_the_touch_controllers_are_active(self, win, remote):
        _drive(remote, 'right', a_click=True, b_click=True, trigger_value=0.9)
        _drive(remote, 'left', a_click=True, b_click=True, trigger_value=0.9)
        _flip_until(win, lambda: all(win.getButtons(button, 'Touch')[0] for button in 'ABXY')
                    and all(v > 0 for v in win.getIndexTriggerValues('Touch')))
        for button in 'ABXY':
            assert win.getButtons(button, 'Xbox')[0] is False
        assert win.getIndexTriggerValues('Xbox') == (0.0, 0.0)
        assert win.getIndexTriggerValues() == (0.0, 0.0)
