import importlib.util


def _is_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False


collect_ignore: list[str] = []

if not _is_available("psychopy"):
    collect_ignore += [
        "eegnb/experiments",
        "eegnb/devices/vr.py",
    ]
elif not _is_available("psychxr"):
    collect_ignore += ["eegnb/devices/vr.py"]
