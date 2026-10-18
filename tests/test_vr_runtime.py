"""Choosing the OpenXR runtime: manifest paths, names matched against the
installed runtimes, and the variable the OpenXR loader reads."""

import gc
import json
import os
import sys

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
