import pytest

from eegnb.devices import cyton
from eegnb.devices import eeg as eeg_module
from eegnb.devices.cyton import (
    GAIN_4X,
    GAIN_12X,
    cyton_ch_config,
    thinkpulse_config,
)


def test_single_gain_sets_every_channel_with_bias_on():
    assert cyton_ch_config(GAIN_4X) == (
        "x1020110Xx2020110Xx3020110Xx4020110X"
        "x5020110Xx6020110Xx7020110Xx8020110X"
    )
    assert cyton_ch_config(GAIN_12X) == (
        "x1050110Xx2050110Xx3050110Xx4050110X"
        "x5050110Xx6050110Xx7050110Xx8050110X"
    )


def test_bias_false_flips_only_the_bias_bit():
    on = cyton_ch_config(GAIN_4X, bias=True)
    off = cyton_ch_config(GAIN_4X, bias=False)
    assert on.replace('1', '0', 1) != on
    for ch in range(1, 9):
        on_ch = f"x{ch}0{GAIN_4X}0110X"
        off_ch = f"x{ch}0{GAIN_4X}0010X"
        assert on_ch in on
        assert off_ch in off


def test_bias_false_does_not_touch_gain_or_srb_bits():
    on = cyton_ch_config(GAIN_12X, bias=True)
    off = cyton_ch_config(GAIN_12X, bias=False)
    assert len(on) == len(off)
    diffs = [i for i, (a, b) in enumerate(zip(on, off)) if a != b]
    assert len(diffs) == 8


def test_bias_accepts_a_per_channel_list():
    bias = [True, True, False, True, True, True, False, True]
    cfg = cyton_ch_config(GAIN_4X, bias=bias)
    for ch in (3, 7):
        assert f"x{ch}0{GAIN_4X}0010X" in cfg
    for ch in (1, 2, 4, 5, 6, 8):
        assert f"x{ch}0{GAIN_4X}0110X" in cfg


def test_bias_list_wrong_length_raises():
    with pytest.raises(ValueError):
        cyton_ch_config(GAIN_4X, bias=[True] * 7)


def test_gains_list_still_supports_per_channel_override():
    gains = [GAIN_4X] * 7 + [GAIN_12X]
    cfg = cyton_ch_config(gains, bias=False)
    assert f"x8{'0'}{GAIN_12X}0010X" in cfg
    assert f"x1{'0'}{GAIN_4X}0010X" in cfg


def test_gains_list_wrong_length_raises():
    with pytest.raises(ValueError):
        cyton_ch_config([GAIN_4X] * 7, bias=False)


def test_thinkpulse_config_defaults_to_gain_4x_bias_on_everywhere():
    assert thinkpulse_config() == cyton_ch_config(GAIN_4X)


def test_thinkpulse_config_excludes_only_the_named_positions():
    cfg = thinkpulse_config(bias_exclude_positions=(5, 7))
    for ch in (5, 7):
        assert f"x{ch}0{GAIN_4X}0010X" in cfg
    for ch in (1, 2, 3, 4, 6, 8):
        assert f"x{ch}0{GAIN_4X}0110X" in cfg


def test_thinkpulse_config_gain_code_is_overridable():
    cfg = thinkpulse_config(gain_code=GAIN_12X, bias_exclude_positions=(5, 7))
    assert f"x10{GAIN_12X}0110X" in cfg
    assert f"x50{GAIN_12X}0010X" in cfg


def test_thinkpulse_config_respects_n_channels():
    cfg = thinkpulse_config(n_channels=4)
    assert cfg.count('x') == 4


def test_thinkpulse_config_no_exclusions_matches_plain_gain_config():
    assert thinkpulse_config(bias_exclude_positions=()) == cyton_ch_config(GAIN_4X)


@pytest.mark.parametrize("latency", [16, None])
def test_ftdi_latency_check_aborts_unless_1ms(monkeypatch, latency):
    monkeypatch.setattr(cyton.sys, "platform", "win32")
    monkeypatch.setattr(cyton, "get_ftdi_latency_ms", lambda port: latency)
    with pytest.raises(RuntimeError):
        cyton.assert_ftdi_latency_1ms("COM3")


def test_ftdi_latency_check_passes_at_1ms(monkeypatch):
    monkeypatch.setattr(cyton.sys, "platform", "win32")
    monkeypatch.setattr(cyton, "get_ftdi_latency_ms", lambda port: 1)
    cyton.assert_ftdi_latency_1ms("COM3")


def test_ftdi_latency_check_skips_non_windows(monkeypatch):
    monkeypatch.setattr(cyton.sys, "platform", "linux")
    monkeypatch.setattr(cyton, "get_ftdi_latency_ms", lambda port: 16)
    cyton.assert_ftdi_latency_1ms("/dev/ttyUSB0")


class _StubBoardShim:
    def __init__(self, board_id, params):
        self.params = params

    @staticmethod
    def get_sampling_rate(board_id):
        return 250

    def prepare_session(self):
        pass


@pytest.mark.parametrize("serial_port, picked", [("COM3", None), (None, "COM7")])
def test_ftdi_latency_check_runs_on_the_port_in_use(monkeypatch, serial_port, picked):
    checked = []
    monkeypatch.setattr(eeg_module, "BoardShim", _StubBoardShim)
    monkeypatch.setattr(eeg_module, "get_openbci_usb", lambda: picked)
    monkeypatch.setattr(eeg_module, "assert_ftdi_latency_1ms", checked.append)
    device = eeg_module.EEG.__new__(eeg_module.EEG)
    device.device_name = "cyton"
    device.serial_port = serial_port
    device.serial_num = None
    device.config = None
    device.analog_mode = False
    device._init_brainflow()
    assert checked == [serial_port or picked]
