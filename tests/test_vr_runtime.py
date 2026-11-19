"""Choosing the OpenXR runtime: manifest paths, names matched against the
installed runtimes, and the variable the OpenXR loader reads."""

import gc
import json
import os
import sys
from types import SimpleNamespace

import pytest

pytest.importorskip("psychopy")

from eegnb.devices import vr
from eegnb.devices.vr import VR, registered_runtimes, resolve_runtime


def _manifest(folder, stem, name=None):
    runtime = {'library_path': f'./{stem}.dll'}
    if name is not None:
        runtime['name'] = name
    path = folder / f'{stem}.json'
    path.write_text(json.dumps({'file_format_version': '1.0.0', 'runtime': runtime}))
    return str(path)


@pytest.fixture
def installed(tmp_path, monkeypatch):
    paths = {
        'oculus': _manifest(tmp_path, 'oculus_openxr_64', 'Oculus OpenXR'),
        'steamvr': _manifest(tmp_path, 'steamxr_win64', 'SteamVR'),
        'virtualdesktop': _manifest(tmp_path, 'virtualdesktop-openxr',
                                    'VirtualDesktopXR (Bundled)'),
    }
    _manifest(tmp_path, 'active_runtime', 'Oculus OpenXR')
    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.setattr(vr, 'LINUX_RUNTIME_DIRS', (str(tmp_path), str(tmp_path / 'missing')))
    return paths


def test_registered_runtimes_reads_manifest_names_and_skips_the_active_link(installed):
    found = registered_runtimes()
    assert found == {installed['oculus']: 'Oculus OpenXR',
                     installed['steamvr']: 'SteamVR',
                     installed['virtualdesktop']: 'VirtualDesktopXR (Bundled)'}


def test_manifest_without_a_name_is_known_by_its_file_name(tmp_path, monkeypatch):
    path = _manifest(tmp_path, 'openxr_monado')
    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.setattr(vr, 'LINUX_RUNTIME_DIRS', (str(tmp_path),))
    assert registered_runtimes() == {path: 'openxr_monado'}
    assert resolve_runtime('Monado') == path


@pytest.mark.parametrize('name', ['oculus', 'SteamVR', 'steamvr', 'virtual-desktop',
                                  'VirtualDesktop'])
def test_name_matches_one_installed_runtime(installed, name):
    key = name.lower().replace('-', '')
    assert resolve_runtime(name) == installed[key]


def test_manifest_path_is_used_as_given(installed, tmp_path):
    elsewhere = tmp_path / 'elsewhere'
    elsewhere.mkdir()
    other = _manifest(elsewhere, 'custom_runtime', 'Custom')
    assert resolve_runtime(other) == os.path.abspath(other)


def test_name_matching_several_runtimes_is_refused(installed):
    with pytest.raises(ValueError, match='matched 2 of'):
        resolve_runtime('openxr')


def test_unknown_name_lists_what_is_installed(installed):
    with pytest.raises(ValueError) as error:
        resolve_runtime('pimax')
    assert 'matched 0 of' in str(error.value)
    assert 'SteamVR' in str(error.value) and installed['oculus'] in str(error.value)


def test_runtime_is_set_for_the_loader_before_openxr_loads(installed, monkeypatch):
    monkeypatch.delenv('XR_RUNTIME_JSON', raising=False)
    monkeypatch.setitem(sys.modules, 'xr', None)
    with pytest.raises(ImportError, match='pyopenxr'):
        VR(runtime='oculus')
    assert os.environ['XR_RUNTIME_JSON'] == installed['oculus']


def test_no_runtime_leaves_the_loader_on_its_default(monkeypatch):
    monkeypatch.delenv('XR_RUNTIME_JSON', raising=False)
    monkeypatch.setitem(sys.modules, 'xr', None)
    with pytest.raises(ImportError):
        VR()
    assert 'XR_RUNTIME_JSON' not in os.environ


def test_failed_construction_does_not_raise_again_on_collection(installed, monkeypatch):
    raised = []
    monkeypatch.setattr(sys, 'unraisablehook', raised.append)
    with pytest.raises(ValueError):
        VR(runtime='pimax')
    gc.collect()
    assert raised == []


class _NoHeadset(Exception):
    pass


def _xr_without_a_headset(destroyed):
    def get_system(instance, get_info):
        raise _NoHeadset

    def build(**kw):
        return kw

    def destroy(handle):
        destroyed.append(handle)

    return SimpleNamespace(
        SessionState=SimpleNamespace(IDLE=0),
        KHR_OPENGL_ENABLE_EXTENSION_NAME='XR_KHR_opengl_enable',
        FB_DISPLAY_REFRESH_RATE_EXTENSION_NAME='XR_FB_display_refresh_rate',
        FB_PASSTHROUGH_EXTENSION_NAME='XR_FB_passthrough',
        KHR_WIN32_CONVERT_PERFORMANCE_COUNTER_TIME_EXTENSION_NAME=(
            'XR_KHR_win32_convert_performance_counter_time'),
        KHR_CONVERT_TIMESPEC_TIME_EXTENSION_NAME='XR_KHR_convert_timespec_time',
        enumerate_instance_extension_properties=lambda: [
            SimpleNamespace(extension_name=b'XR_KHR_opengl_enable')],
        ApplicationInfo=build, InstanceCreateInfo=build, SystemGetInfo=build,
        FormFactor=SimpleNamespace(HEAD_MOUNTED_DISPLAY=1),
        create_instance=lambda create_info: 'instance',
        get_system=get_system,
        destroy_swapchain=destroy, destroy_passthrough_layer_fb=destroy,
        destroy_passthrough_fb=destroy, destroy_action_set=destroy,
        destroy_space=destroy, destroy_session=destroy, destroy_instance=destroy)


class _SessionFailed(Exception):
    pass


def _xr_failing_after_the_window(log):
    xr = _xr_without_a_headset(log)

    def create_session(instance, create_info):
        raise _SessionFailed

    xr.get_system = lambda instance, get_info: 'system'
    xr.get_instance_properties = lambda instance: SimpleNamespace(
        runtime_name=b'test', runtime_version=1)
    xr.Version = str
    xr.get_system_properties = lambda instance, system_id: SimpleNamespace(system_name=b'hmd')
    xr.ViewConfigurationType = SimpleNamespace(PRIMARY_STEREO=2)
    xr.enumerate_view_configuration_views = lambda **kw: [
        SimpleNamespace(recommended_image_rect_width=64, recommended_image_rect_height=48)] * 2
    xr.SessionCreateInfo = lambda **kw: kw
    xr.create_session = create_session
    return xr


@pytest.fixture
def desktop_window(monkeypatch):
    log = []

    def opened(self, size, **kwargs):
        self._closed = False
        self.clientSize = size
        self.winHandle = SimpleNamespace(switch_to=lambda: None, set_vsync=lambda on: None,
                                         activate=lambda: None)
        log.append('window opened')

    def closed(self):
        self._closed = True
        log.append('window closed')

    monkeypatch.delenv('XR_RUNTIME_JSON', raising=False)
    monkeypatch.setattr(vr.visual.Window, '__init__', opened)
    monkeypatch.setattr(vr.visual.Window, 'close', closed)
    monkeypatch.setitem(sys.modules, 'xr.utils.gl', SimpleNamespace(
        OpenGLGraphics=lambda instance, system_id, context: SimpleNamespace(
            graphics_binding=SimpleNamespace(pointer=None))))
    return log


def test_instance_is_destroyed_when_the_headset_is_unavailable(monkeypatch, desktop_window):
    monkeypatch.setitem(sys.modules, 'xr', _xr_without_a_headset(desktop_window))
    with pytest.raises(_NoHeadset):
        VR()
    assert desktop_window == ['instance']


def test_failure_after_the_window_opened_closes_it_after_the_openxr_handles(
        monkeypatch, desktop_window):
    monkeypatch.setitem(sys.modules, 'xr', _xr_failing_after_the_window(desktop_window))
    with pytest.raises(_SessionFailed):
        VR()
    assert desktop_window == ['window opened', 'instance', 'window closed']


def test_windows_reads_the_khronos_available_runtimes_key(tmp_path, monkeypatch):
    manifest = _manifest(tmp_path, 'oculus_openxr_64', 'Oculus OpenXR')
    stale = str(tmp_path / 'uninstalled.json')
    opened = []

    class _Key:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class _Winreg:
        HKEY_LOCAL_MACHINE = 'HKLM'

        @staticmethod
        def OpenKey(root, path):
            opened.append((root, path))
            return _Key()

        @staticmethod
        def EnumValue(key, index):
            values = [(manifest, 0, 4), (stale, 0, 4)]
            if index >= len(values):
                raise OSError
            return values[index]

    monkeypatch.setattr(sys, 'platform', 'win32')
    monkeypatch.setitem(sys.modules, 'winreg', _Winreg)
    assert registered_runtimes() == {manifest: 'Oculus OpenXR'}
    assert opened == [('HKLM', r'SOFTWARE\Khronos\OpenXR\1\AvailableRuntimes')]
