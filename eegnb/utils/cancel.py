"""Cross-platform stdin-based cancel prompt.

Replaces ``pynput.keyboard.Listener`` for the simple case of "give the
user N seconds to press a key + Enter to cancel an operation". Uses a
daemon thread reading from stdin so it works on Linux / macOS / Windows
and in terminals without a ``DISPLAY``.

pynput was dropped because it pulls in evdev (Linux) which currently
fails to build from source under several common toolchains.
"""

from __future__ import annotations

import sys
import threading


def wait_for_cancel(timeout: float, cancel_key: str = "c") -> bool:
    """Block for up to ``timeout`` seconds waiting for the user to type
    ``cancel_key`` + Enter on stdin.

    Returns True if cancel was requested, False if the timeout elapsed.
    """
    cancel_event = threading.Event()
    cancel_key = cancel_key.strip().lower()

    def _reader() -> None:
        try:
            line = sys.stdin.readline()
        except (OSError, ValueError):
            return
        if line and line.strip().lower() == cancel_key:
            cancel_event.set()

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()
    cancel_event.wait(timeout=timeout)
    return cancel_event.is_set()
