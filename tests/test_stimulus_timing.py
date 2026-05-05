"""
Refined benchmark script for measuring stimulus timing latency and jitter in EEG-ExPy.
This script measures the "round-trip" latency of LSL markers and the precision
of timestamps relative to the actual receipt time.
"""

import os
import sys
import time
from pathlib import Path
import threading

import numpy as np
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_byprop, local_clock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from eegnb.experiments.visual_mindeye.visual_mindeye import VisualMindEye

class MockEEG:
    """Mock EEG device that pushes to a local LSL stream."""
    def __init__(self, outlet):
        self.outlet = outlet
        self.backend = "muselsl"
        self.device_name = "mock"

    def push_sample(self, marker, timestamp):
        self.outlet.push_sample(marker, timestamp)

def run_timing_benchmark():
    print("=== EEG-ExPy Stimulus Timing Benchmark (Refined) ===")
    
    # 1. Create a local LSL outlet for markers
    info = StreamInfo('TestMarkers', 'Markers', 1, 0, 'string', 'test_uid_456')
    outlet = StreamOutlet(info)
    
    # 2. Resolve the inlet (self-listening)
    print("Connecting to local marker stream...")
    streams = resolve_byprop('name', 'TestMarkers', timeout=2)
    if not streams:
        print("Error: Could not find local LSL stream.")
        return
    inlet = StreamInlet(streams[0])
    
    mock_eeg = MockEEG(outlet)
    exp = VisualMindEye(duration=5, eeg=mock_eeg, n_trials=20)
    
    latencies_software = []  # Time between local_clock() call and push_sample finishing
    latencies_lsl_sync = []  # Difference between intended_ts and received_ts (should be 0 or small)
    latencies_round_trip = [] # Time between push and actual receipt in inlet
    
    print("\nRunning Benchmark trials...")
    
    for i in range(exp.n_trials):
        # Measure Software Latency
        t_before = local_clock()
        exp.eeg.push_sample(marker=['1'], timestamp=t_before)
        t_after = local_clock()
        
        # Pull from inlet
        # Note: LSL might be buffered, so we pull with a short wait
        sample, stream_ts = inlet.pull_sample(timeout=1.0)
        t_received = local_clock()
        
        if sample:
            sw_lat = (t_after - t_before) * 1000
            sync_lat = (stream_ts - t_before) * 1000
            rt_lat = (t_received - t_before) * 1000
            
            latencies_software.append(sw_lat)
            latencies_lsl_sync.append(sync_lat)
            latencies_round_trip.append(rt_lat)
            
            if i % 5 == 0 or i == exp.n_trials - 1:
                print(f"  Trial {i+1:2d}: SW={sw_lat:.3f}ms, Sync={sync_lat:.3f}ms, RT={rt_lat:.3f}ms")
        else:
            print(f"  Trial {i+1:2d}: FAILED")
            
        time.sleep(0.05) # Fast trials
        
    print("\n--- Summary (ms) ---")
    print(f"Software (Push duration):  Mean={np.mean(latencies_software):.4f}, Std={np.std(latencies_software):.4f}")
    print(f"LSL Sync (Intended-Stream): Mean={np.mean(latencies_lsl_sync):.4f}, Std={np.std(latencies_lsl_sync):.4f}")
    print(f"Round Trip (Push-Receive): Mean={np.mean(latencies_round_trip):.4f}, Std={np.std(latencies_round_trip):.4f}")
    
    # Analyze Jitter
    jitter = np.std(latencies_round_trip)
    if jitter < 1.0:
        print(f"STATUS: PASS (Low Jitter: {jitter:.4f} ms)")
    else:
        print(f"STATUS: WARNING (High Jitter: {jitter:.4f} ms)")

if __name__ == "__main__":
    run_timing_benchmark()
