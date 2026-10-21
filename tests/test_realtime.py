"""The Windows 1 ms timer request survives a hidden stimulus window."""

import ctypes
from types import SimpleNamespace

import pytest

pytest.importorskip("psychopy")

from eegnb.experiments import realtime


def test_timer_opt_out_is_a_no_op_off_windows(monkeypatch):
    monkeypatch.setattr(realtime.sys, 'platform', 'linux')
    assert realtime.honour_timer_resolution_when_hidden() is False


def test_timer_opt_out_clears_the_ignore_timer_resolution_throttle(monkeypatch):
    calls = []

    class _Function:
        def __init__(self, name):
            self.name = name

        def __call__(self, *args):
            if self.name == 'GetCurrentProcess':
                return -1
            state = ctypes.cast(args[2], ctypes.POINTER(ctypes.c_ulong * 3)).contents
            calls.append((args[1], tuple(state)))
            return 1

    class _Kernel32:
        def __init__(self, *args, **kwargs):
            self.GetCurrentProcess = _Function('GetCurrentProcess')
            self.SetProcessInformation = _Function('SetProcessInformation')

    monkeypatch.setattr(realtime.sys, 'platform', 'win32')
    monkeypatch.setattr(ctypes, 'WinDLL', _Kernel32, raising=False)
    assert realtime.honour_timer_resolution_when_hidden() is True
    assert calls == [(4, (1, 0x4, 0))]


def test_high_res_timer_opts_out_before_raising_the_tick(monkeypatch):
    order = []
    monkeypatch.setattr(realtime.sys, 'platform', 'win32')
    monkeypatch.setattr(realtime, 'honour_timer_resolution_when_hidden',
                        lambda: order.append('opt-out') or True)
    winmm = SimpleNamespace(timeBeginPeriod=lambda ms: order.append(('begin', ms)))
    monkeypatch.setattr(ctypes, 'windll', SimpleNamespace(winmm=winmm), raising=False)
    assert realtime.force_high_res_timer() is True
    assert order == ['opt-out', ('begin', 1)]
