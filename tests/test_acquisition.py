import time
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowPresets

from eegnb.devices.eeg import EEG, MUSE_BRAINFLOW_PPG_COMMANDS, muse_sidecar_path


def test_synthetic_acquisition(tmp_path):
    """
    Test the data acquisition pipeline using a synthetic BrainFlow board.
    This verifies that we can initialize a device, start a stream, 
    record data, and save it to a CSV file in a CI-friendly way.
    """
    # Use a temporary file for recording
    save_fn = tmp_path / "synthetic_data.csv"
    
    # Initialize EEG with synthetic board
    # BrainFlow synthetic board (ID -1) works without hardware
    eeg = EEG(device='synthetic')
    
    # Verify metadata initialization
    assert eeg.backend == 'brainflow'
    assert eeg.sfreq == 250  # Default for synthetic board
    assert len(eeg.channels) > 0
    
    # Start stream and capture data
    # We specify a short duration for the test
    record_duration = 2
    eeg.start(str(save_fn), duration=record_duration + 5)
    
    # Simulate some experiment time
    time.sleep(record_duration)
    
    # Push a few synthetic markers
    eeg.push_sample(marker=1, timestamp=time.time())
    time.sleep(0.1)
    eeg.push_sample(marker=2, timestamp=time.time())
    
    # Stop recording and release session
    eeg.stop()
    
    # Verify file creation and content
    assert save_fn.exists()
    
    # Read the data back
    data = pd.read_csv(save_fn)
    
    # Basic data validation
    assert len(data) > 0
    assert 'timestamps' in data.columns
    assert 'stim' in data.columns
    
    # Check if markers were recorded (may vary slightly based on timing)
    # but we should at least see non-zero values in the stim column
    assert (data['stim'] != 0).any()

    # Non-Muse boards should not grow sidecar files
    assert not Path(muse_sidecar_path(save_fn, "ppg")).exists()
    assert not Path(muse_sidecar_path(save_fn, "accel")).exists()
    
    print(f"Acquired {len(data)} samples with columns: {list(data.columns)}")


def test_muse_sidecar_path():
    path = Path("recording_2026-01-01-12.00.00.csv")
    assert Path(muse_sidecar_path(path, "ppg")).name == "recording_2026-01-01-12.00.00_ppg.csv"
    assert Path(muse_sidecar_path(path, "accel")).name == "recording_2026-01-01-12.00.00_accel.csv"


def test_muse_ppg_commands_keep_four_eeg_channels():
    assert MUSE_BRAINFLOW_PPG_COMMANDS["muse2_bfn"] == "p51"
    assert MUSE_BRAINFLOW_PPG_COMMANDS["muse2_bfb"] == "p51"
    assert MUSE_BRAINFLOW_PPG_COMMANDS["museS_bfn"] == "p61"
    assert MUSE_BRAINFLOW_PPG_COMMANDS["museS_bfb"] == "p61"
    assert "muse2016_bfn" not in MUSE_BRAINFLOW_PPG_COMMANDS


def _fake_muse_eeg(device_name="muse2_bfn"):
    eeg = EEG.__new__(EEG)
    eeg.device_name = device_name
    eeg.brainflow_id = BoardIds.MUSE_2_BOARD.value
    eeg.sfreq = BoardShim.get_sampling_rate(eeg.brainflow_id)
    eeg.ch_names = ["TP9", "AF7", "AF8", "TP10"]
    eeg.markers = []
    eeg.stream_started = True
    return eeg


def _preset_array(board_id, preset, n_samples, fill=1.0):
    n_rows = BoardShim.get_num_rows(board_id, preset)
    data = np.full((n_rows, n_samples), fill, dtype=float)
    ts_idx = BoardShim.get_timestamp_channel(board_id, preset)
    data[ts_idx] = np.arange(n_samples, dtype=float)
    return data


def test_enable_muse_ppg_stream_uses_p51_for_muse2():
    eeg = _fake_muse_eeg("muse2_bfn")
    eeg.board = MagicMock()
    eeg._enable_muse_ppg_stream()
    eeg.board.config_board.assert_called_once_with("p51")


def test_enable_muse_ppg_stream_uses_p61_for_muses():
    eeg = _fake_muse_eeg("museS_bfn")
    eeg.brainflow_id = BoardIds.MUSE_S_BOARD.value
    eeg.board = MagicMock()
    eeg._enable_muse_ppg_stream()
    eeg.board.config_board.assert_called_once_with("p61")


def test_stop_brainflow_writes_muse_sidecars(tmp_path):
    board_id = BoardIds.MUSE_2_BOARD.value
    sfreq = BoardShim.get_sampling_rate(board_id)
    aux_sfreq = BoardShim.get_sampling_rate(board_id, BrainFlowPresets.AUXILIARY_PRESET)
    anc_sfreq = BoardShim.get_sampling_rate(board_id, BrainFlowPresets.ANCILLARY_PRESET)

    eeg_data = _preset_array(board_id, BrainFlowPresets.DEFAULT_PRESET, 5 * sfreq + 10, 1.0)
    aux_data = _preset_array(board_id, BrainFlowPresets.AUXILIARY_PRESET, 5 * aux_sfreq + 5, 2.0)
    anc_data = _preset_array(board_id, BrainFlowPresets.ANCILLARY_PRESET, 5 * anc_sfreq + 5, 3.0)

    def get_board_data(num_samples=None, preset=BrainFlowPresets.DEFAULT_PRESET):
        if preset == BrainFlowPresets.AUXILIARY_PRESET:
            return aux_data
        if preset == BrainFlowPresets.ANCILLARY_PRESET:
            return anc_data
        return eeg_data

    board = MagicMock()
    board.get_board_data.side_effect = get_board_data

    eeg = _fake_muse_eeg()
    eeg.board = board
    save_fn = tmp_path / "recording_2026-01-01.csv"
    eeg.save_fn = str(save_fn)

    eeg._stop_brainflow()

    assert save_fn.exists()
    data = pd.read_csv(save_fn)
    assert "timestamps" in data.columns
    assert "stim" in data.columns
    assert "TP9" in data.columns
    assert not any("ppg" in col.lower() for col in data.columns)

    ppg_path = Path(muse_sidecar_path(save_fn, "ppg"))
    accel_path = Path(muse_sidecar_path(save_fn, "accel"))
    assert ppg_path.exists()
    assert accel_path.exists()

    ppg = pd.read_csv(ppg_path)
    accel = pd.read_csv(accel_path)
    assert "timestamps" in ppg.columns
    assert any(col.startswith("ppg_") for col in ppg.columns)
    assert "timestamps" in accel.columns
    assert any(col.startswith("accel_") for col in accel.columns)

    board.stop_stream.assert_called_once()
    board.release_session.assert_called_once()


def test_stop_brainflow_saves_eeg_if_sidecars_fail(tmp_path):
    board_id = BoardIds.MUSE_2_BOARD.value
    sfreq = BoardShim.get_sampling_rate(board_id)
    eeg_data = _preset_array(board_id, BrainFlowPresets.DEFAULT_PRESET, 5 * sfreq + 10, 1.0)

    def get_board_data(num_samples=None, preset=BrainFlowPresets.DEFAULT_PRESET):
        if preset != BrainFlowPresets.DEFAULT_PRESET:
            raise RuntimeError("preset unavailable")
        return eeg_data

    board = MagicMock()
    board.get_board_data.side_effect = get_board_data

    eeg = _fake_muse_eeg()
    eeg.board = board
    save_fn = tmp_path / "recording_2026-01-01.csv"
    eeg.save_fn = str(save_fn)

    eeg._stop_brainflow()

    assert save_fn.exists()
    data = pd.read_csv(save_fn)
    assert "timestamps" in data.columns
    assert "stim" in data.columns
    assert not Path(muse_sidecar_path(save_fn, "ppg")).exists()
    assert not Path(muse_sidecar_path(save_fn, "accel")).exists()
