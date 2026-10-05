import sys
from typing import Sequence, Union

GAIN_1X, GAIN_2X, GAIN_4X, GAIN_6X, GAIN_8X, GAIN_12X, GAIN_24X = range(7)


def cyton_ch_config(gains, n_channels: int = 8,
                    bias: Union[bool, Sequence[bool]] = True) -> str:
    if isinstance(gains, int):
        gains = [gains] * n_channels
    elif len(gains) != n_channels:
        raise ValueError(f"gains has {len(gains)} entries, expected {n_channels}")
    if isinstance(bias, bool):
        bias = [bias] * n_channels
    elif len(bias) != n_channels:
        raise ValueError(f"bias has {len(bias)} entries, expected {n_channels}")
    return "".join(f"x{ch}0{g}0{'1' if b else '0'}10X"
                   for ch, g, b in zip(range(1, n_channels + 1), gains, bias))


def thinkpulse_config(n_channels: int = 8, gain_code: int = GAIN_4X,
                      bias_exclude_positions: Sequence[int] = ()) -> str:
    bias = [pos not in set(bias_exclude_positions) for pos in range(1, n_channels + 1)]
    return cyton_ch_config(gain_code, n_channels=n_channels, bias=bias)


def get_ftdi_latency_ms(com_port: str):
    if sys.platform != 'win32':
        return None
    import winreg
    ftdi_root = r"SYSTEM\CurrentControlSet\Enum\FTDIBUS"
    target = com_port.upper()
    try:
        root_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ftdi_root)
    except OSError:
        return None
    try:
        for i in range(1024):
            try:
                device_name = winreg.EnumKey(root_key, i)
            except OSError:
                break
            device_path = f"{ftdi_root}\\{device_name}"
            try:
                device_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, device_path)
            except OSError:
                continue
            try:
                for j in range(64):
                    try:
                        instance = winreg.EnumKey(device_key, j)
                    except OSError:
                        break
                    params_path = f"{device_path}\\{instance}\\Device Parameters"
                    try:
                        params_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, params_path)
                    except OSError:
                        continue
                    try:
                        port_name, _ = winreg.QueryValueEx(params_key, "PortName")
                        if str(port_name).upper() == target:
                            latency, _ = winreg.QueryValueEx(params_key, "LatencyTimer")
                            return int(latency)
                    except OSError:
                        pass
                    finally:
                        params_key.Close()
            finally:
                device_key.Close()
    finally:
        root_key.Close()
    return None


def assert_ftdi_latency_1ms(com_port: str) -> None:
    if sys.platform != 'win32':
        return
    latency = get_ftdi_latency_ms(com_port)
    if latency is None:
        raise RuntimeError(
            f"Could not read FTDI LatencyTimer for {com_port}. "
            f"Verify it is an FTDI device in Device Manager."
        )
    if latency != 1:
        raise RuntimeError(
            f"FTDI LatencyTimer for {com_port} is {latency} ms; required 1 ms. "
            f"Device Manager -> Ports -> USB Serial Port ({com_port}) -> "
            f"Properties -> Port Settings -> Advanced -> Latency Timer (ms) = 1. "
            f"See https://docs.openbci.com/Troubleshooting/FTDI_Fix_Windows/"
        )
