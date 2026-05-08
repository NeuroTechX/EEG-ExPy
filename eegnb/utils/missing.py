"""Sentinel objects for optional dependencies.

Lets the package import cleanly even when an optional library isn't installed,
while still raising a clear, actionable error if a user tries to use a feature
that depends on it.

Two flavours:
    missing_class(...)   — for symbols the user *instantiates* (e.g. an
                            Experiment subclass). Raises on construction.
    missing_module(...)  — for symbols the user *accesses attributes on*
                            (e.g. ``pyxid2.get_xid_devices()``). Raises on
                            any attribute access.
"""


from typing import Any


def _format_message(name: str, feature: str, extras: str) -> str:
    return (
        f"{name} is not installed. {feature} is not available in this "
        f"environment. Please install the '{extras}' or 'full' dependencies "
        "to use this feature."
    )


def missing_class(name: str, feature: str, extras: str) -> Any:
    """Sentinel mimicking a class; raises RuntimeError on instantiation.

    Returns ``Any`` so the sentinel can be assigned to a name that would
    normally hold a specific class (e.g. ``VisualN170 = missing_class(...)``)
    without type-checker complaints at the call site.
    """
    message = _format_message(name, feature, extras)

    class _Missing:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(message)

    return _Missing


def missing_module(name: str, feature: str, extras: str) -> Any:
    """Sentinel mimicking a module; raises RuntimeError on attribute access.

    Returns ``Any`` so the sentinel can be assigned to a name that would
    normally hold a real module (e.g. ``pyxid2 = missing_module(...)``)
    without type-checker complaints at the call site.
    """
    message = _format_message(name, feature, extras)

    class _Missing:
        def __getattr__(self, attr):
            raise RuntimeError(message)

    return _Missing()
