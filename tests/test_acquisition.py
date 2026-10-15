import os
import time
import pandas as pd
import pytest
from eegnb.devices.eeg import EEG

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


def test_muse_push_sample_wraps_a_scalar_but_leaves_a_list_alone():
    """EEG._muse_push_sample sends a single-channel [marker] to the LSL outlet:
    a scalar is wrapped, an already-wrapped list passes through (P300 path)."""

    class FakeOutlet:
        def __init__(self):
            self.last = None

        def push_sample(self, marker, timestamp):
            self.last = marker

    outlet = FakeOutlet()
    eeg = object.__new__(EEG)                 # skip __init__ (it would connect hardware)
    eeg.muse_StreamOutlet = outlet

    eeg._muse_push_sample(2, 123.0)
    assert outlet.last == [2]                 # scalar -> single-channel list

    eeg._muse_push_sample([2], 123.0)
    assert outlet.last == [2]                 # already a list -> unchanged
