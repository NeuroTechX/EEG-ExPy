"""Process-priority / OS-scheduler helpers for time-critical sections.

Three independent settings affect frame pacing; ``high_priority_section`` raises
all three on entry and restores them on exit. The scheduler-tick setting is
Windows-only (Linux/macOS already run a ≤1 ms tick); process priority and GC
suspension apply on all platforms:

  - Scheduler tick: Windows' default is 15.625 ms, and every ``time.sleep``
    (including libovr's ``waitToBeginFrame``) rounds up to it, mathematically
    locking a 120 Hz / 8.33 ms render loop to half-rate and dropping every
    other frame. ``timeBeginPeriod(1)``
    drops it to 1 ms; ``timeEndPeriod(1)`` restores it so the change stays
    scoped to the section rather than held process-wide.
  - Process priority: ``core.rush(True)`` → SetPriorityClass(HIGH_PRIORITY_CLASS).
  - Python GC: ``gc.disable()`` suspends the generational collector.

"""

from __future__ import annotations

import gc
import logging
import sys
from contextlib import contextmanager

from psychopy import core

logger = logging.getLogger(__name__)


def force_high_res_timer() -> bool:
    """Raise the Windows scheduler tick to 1 ms via ``timeBeginPeriod(1)`` (see
    module docstring for why). No-op off Windows.

    Must be paired with ``end_high_res_timer`` to release the tick;
    ``high_priority_section`` does this for you. Returns ``True`` if the tick was
    raised (caller owes a matching ``end_high_res_timer``), ``False`` otherwise.
    """
    if sys.platform != 'win32':
        return False
    try:
        import ctypes
        ctypes.windll.winmm.timeBeginPeriod(1)
        logger.info("[timer] timeBeginPeriod(1)")
        return True
    except Exception as e:
        logger.warning("[timer] timeBeginPeriod failed: %s", e)
        return False


def end_high_res_timer() -> None:
    """Release a 1 ms tick raised by ``force_high_res_timer`` via
    ``timeEndPeriod(1)``. No-op off Windows."""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        ctypes.windll.winmm.timeEndPeriod(1)
    except Exception as e:
        logger.warning("[timer] timeEndPeriod failed: %s", e)


def query_timer_resolution_ms():
    """Return current system timer resolution in ms (None on non-Windows
    or query failure). Resolution is reported in 100-ns units by
    ``NtQueryTimerResolution``."""
    if sys.platform != 'win32':
        return None
    try:
        import ctypes
        from ctypes import wintypes
        ntdll = ctypes.windll.ntdll
        _min = wintypes.ULONG(); _max = wintypes.ULONG(); _cur = wintypes.ULONG()
        ntdll.NtQueryTimerResolution(
            ctypes.byref(_min), ctypes.byref(_max), ctypes.byref(_cur)
        )
        return _cur.value / 10000.0  # 100-ns → ms
    except Exception:
        return None


@contextmanager
def high_priority_section():
    """Time-critical mode for the wrapped block: raises the three settings described
    in the module docstring on entry and restores them on exit. Use around any
    precision-timed section — the trial loop, frame-rate validation, etc.
    """
    raised = force_high_res_timer()
    core.rush(True)
    gc.disable()
    try:
        yield
    finally:
        gc.enable()
        core.rush(False)
        if raised:
            end_high_res_timer()
