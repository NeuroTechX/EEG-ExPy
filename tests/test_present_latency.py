"""
Benchmark script for measuring the internal latency of the present_stimulus method.
This helps identify bottlenecks in the Python code itself, separate from hardware/LSL.
"""

import time
from unittest.mock import MagicMock
import numpy as np
import sys
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from eegnb.experiments.visual_mindeye.visual_mindeye import VisualMindEye
from eegnb.experiments.visual_floc.visual_floc import VisualfLoc

def bench_experiment_logic(exp_class, name):
    print(f"\n=== {name} Logic Benchmark ===")
    
    # Mock EEG and Window
    mock_eeg = MagicMock()
    mock_eeg.backend = "muselsl"
    mock_win = MagicMock()
    
    # Instantiate Experiment
    exp = exp_class(eeg=mock_eeg, n_trials=100)
    exp.window = mock_win
    
    # Mock pre-loaded stimuli and dependencies
    if name == "VisualMindEye":
        exp.stim_cache = {f"img{i}": MagicMock() for i in range(10)}
        exp.stim = [f"img{i%10}" for i in range(100)]
        exp.conditions = pd.DataFrame({'is_repeat': [0, 1] * 50})
    else: # fLoc
        exp.stim_cache = {cat: [MagicMock() for _ in range(5)] for cat in exp.categories}
        exp.markernames = [1, 2, 3, 4, 5]
        exp.trials = pd.DataFrame({'parameter': [i % 5 for i in range(100)]})
    
    latencies = []
    for i in range(100):
        t0 = time.time()
        exp.present_stimulus(i, None)
        latencies.append(time.time() - t0)
        
    mean_ms = np.mean(latencies) * 1000
    std_ms = np.std(latencies) * 1000
    print(f"Mean Execution Latency: {mean_ms:.4f} ms")
    print(f"Jitter (Std): {std_ms:.4f} ms")
    
    if mean_ms < 1.0:
        print("STATUS: PASS (High Efficiency)")
    else:
        print("STATUS: WARNING (Code logic taking > 1ms)")

if __name__ == "__main__":
    bench_experiment_logic(VisualMindEye, "VisualMindEye")
    bench_experiment_logic(VisualfLoc, "VisualfLoc")
