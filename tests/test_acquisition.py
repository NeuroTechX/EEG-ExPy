import os
import time
import numpy as np
import pandas as pd
import pytest
from brainflow.board_shim import BoardIds, BoardShim
from eegnb.devices.eeg import EEG


@pytest.mark.parametrize(("other", "expected"), [
    (None, "preset=p1041;low_latency=true"),
    ("p21", "preset=p21;low_latency=true"),
    ("preset=p1042", "preset=p1042;low_latency=true"),
    ("preset=p21;low_latency=true", "preset=p21;low_latency=true"),
    ("preset=p21;low_latency=false", "preset=p21;low_latency=false"),
])
def test_muse_s_athena_initialization(monkeypatch, other, expected):
    monkeypatch.setattr(BoardShim, "prepare_session", lambda self: None)
    eeg = EEG(device="museS_athena_bfn", mac_addr="00:11:22:33:44:55",
              serial_num="Muse-Test", other=other)

    assert eeg.backend == "brainflow"
    assert eeg.brainflow_id == BoardIds.MUSE_S_ATHENA_BOARD.value
    assert eeg.sfreq == 256
    assert eeg.n_channels == 4
    assert eeg.channels == ["TP9", "AF7", "AF8", "TP10"]
    assert eeg.brainflow_params.serial_number == "Muse-Test"
    assert eeg.brainflow_params.mac_address == "00:11:22:33:44:55"
    assert eeg.brainflow_params.other_info == expected


@pytest.mark.parametrize("combined", [False, True])
def test_athena_records_all_presets(tmp_path, monkeypatch, combined):
    monkeypatch.setattr(BoardShim, "prepare_session", lambda self: None)
    eeg = EEG(device="museS_athena_bfn", include_all_streams=combined)
    monkeypatch.setattr("eegnb.devices.eeg.sleep", lambda seconds: None)
    for method in ("start_stream", "stop_stream", "release_session"):
        monkeypatch.setattr(eeg.board, method, lambda: None)

    def samples(count, preset):
        desc = BoardShim.get_board_descr(eeg.brainflow_id, preset)
        data = np.arange(desc["num_rows"] * count, dtype=float).reshape(-1, count)
        data[desc["timestamp_channel"]] = 1000 + np.arange(count) / desc["sampling_rate"]
        return data

    monkeypatch.setattr(eeg.board, "get_current_board_data", samples)
    monkeypatch.setattr(eeg.board, "get_board_data", lambda preset: samples(
        6 * BoardShim.get_sampling_rate(eeg.brainflow_id, preset), preset))
    eeg.start(tmp_path / "trial.csv")
    frames = eeg.get_recent_streams()
    names = ["default", "auxiliary", "ancillary"]
    assert [frames[name].shape for name in names] == [(256, 10), (52, 8), (64, 19)]
    assert frames["default"]["other_4"].iloc[0] == 8 * 256
    assert frames["auxiliary"]["gyro_z"].iloc[0] == 6 * 52
    assert frames["ancillary"]["optical_16"].iloc[0] == 16 * 64
    assert frames["ancillary"]["battery"].iloc[0] == 17 * 64
    recent = eeg.get_recent()
    assert recent.shape == (256, 31)
    np.testing.assert_allclose(recent.index, frames["default"].index)
    assert recent["gyro_z"].iloc[1] == pytest.approx(6 * 53 + 52 / 256)
    assert recent["optical_16"].iloc[1] == pytest.approx(16 * 65 + 0.25)
    assert recent["battery"].iloc[1] == 17 * 65
    eeg.markers = [[7, 1005.0]]
    eeg.stop()

    for name, frame in frames.items():
        saved = pd.read_csv(tmp_path / "trial_streams" / (name + ".csv"), index_col=0)
        assert list(saved.columns) == list(frame.columns)
        assert len(saved) == 6 * len(frame)
        np.testing.assert_allclose(saved.index[:len(frame)], frame.index)
    trial = pd.read_csv(tmp_path / "trial.csv")
    assert len(trial) == 256
    assert trial["stim"].iloc[0] == 7
    if combined:
        assert list(trial.columns) == ["timestamps", *recent.columns, "stim"]
        assert trial["optical_16"].iloc[1] == pytest.approx(16 * 384 + 320.25)
        assert pd.isna(trial["optical_16"].iloc[-1])
    else:
        assert list(trial.columns) == ["timestamps", *eeg.channels, "stim"]

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
    
    print(f"Acquired {len(data)} samples with columns: {list(data.columns)}")
