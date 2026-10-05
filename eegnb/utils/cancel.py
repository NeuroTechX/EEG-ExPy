"""Cross-platform stdin-based cancel prompt.

Replaces ``pynput.keyboard.Listener`` for the simple case of "give the
user N seconds to press a key + Enter to cancel an operation". Uses a
daemon thread reading from stdin so it works on Linux / macOS / Windows
and in terminals without a ``DISPLAY`` (e.g. headless rigs over SSH, or CI).

pynput was dropped because it pulls in evdev (Linux) which currently
fails to build from source under several common toolchains.
"""

from __future__ import annotations

import queue
import sys
import threading
import time

# stdin.readline() has no timeout, so one daemon thread reads lines into this
# queue and each prompt waits on the queue with its own deadline.
_lines: queue.Queue[str] = queue.Queue()
_reader_started = threading.Event()


def _ensure_reader() -> None:
    if _reader_started.is_set():
        return
    _reader_started.set()

    def _pump() -> None:
        while True:
            try:
                line = sys.stdin.readline()
            except (OSError, ValueError):
                return
            if line == "":  # EOF
                return
            _lines.put(line)

    threading.Thread(target=_pump, name="eegnb-stdin-cancel", daemon=True).start()


def wait_for_cancel(timeout: float, cancel_key: str = "c") -> bool:
    """Block for up to ``timeout`` seconds waiting for the user to type
    ``cancel_key`` + Enter on stdin.

    Returns True if cancel was requested, False if the timeout elapsed.
    """
    _ensure_reader()
    key = cancel_key.strip().lower()

    # discard input typed before this prompt
    while True:
        try:
            _lines.get_nowait()
        except queue.Empty:
            break

    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        try:
            line = _lines.get(timeout=remaining)
        except queue.Empty:
            return False
        if line.strip().lower() == key:
            return True
