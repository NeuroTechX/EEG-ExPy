""" eeg-notebooks/eegnb/experiments/visual_mindeye/visual_mindeye.py """

import os
from time import time
from pathlib import Path
from psychopy import visual
import pandas as pd
from typing import Optional

from eegnb.devices.eeg import EEG
from eegnb.experiments import Experiment
from eegnb.stimuli import MINDEYE_STIMULI, RT_MINDEYE_DIR

# Default paths relative to the user's home/Workspace if not provided
DEFAULT_STIMULI_DIR = MINDEYE_STIMULI
DEFAULT_CONDITIONS_FILE = RT_MINDEYE_DIR / "psychopy_task" / "conditions_files" / "participant0_.csv"

class VisualMindEye(Experiment.BaseExperiment):
    """
    MindEye experiment for EEG-ExPy.
    Replicates the Natural Scenes Dataset (NSD) paradigm:
    3s image presentation, 1s blank/ITI.
    """

    def __init__(self, duration=120, eeg: Optional[EEG]=None, save_fn=None,
                 n_trials=None, iti=1.0, soa=3.0, jitter=0.0, use_vr=False,
                 stimuli_dir: Optional[str] = None, 
                 conditions_file: Optional[str] = None):
        
        # Set experiment name
        exp_name = "Visual MindEye"
        
        self.stimuli_dir = Path(stimuli_dir) if stimuli_dir else DEFAULT_STIMULI_DIR
        self.conditions_file = Path(conditions_file) if conditions_file else DEFAULT_CONDITIONS_FILE
        
        if not self.conditions_file.exists():
            print(f"Warning: Conditions file not found at {self.conditions_file}")
            self.conditions = pd.DataFrame(columns=['current_image', 'is_repeat'])
        else:
            self.conditions = pd.read_csv(self.conditions_file)
            
        if n_trials is None:
            n_trials = len(self.conditions)
            
        super(VisualMindEye, self).__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr)

    def load_stimulus(self):
        """
        Loads the stimuli images based on the conditions file.
        Pre-loads unique images to ensure high-precision timing.
        """
        if self.conditions.empty:
            return []

        image_names = self.conditions['current_image'].unique()
        self.stim_cache = {}
        
        # Base path for fallback images in rt_mindEye2
        fallback_base = RT_MINDEYE_DIR / "psychopy_task"
        
        print(f"Pre-loading {len(image_names)} unique images for MindEye...")
        
        for name in image_names:
            if "blank.jpg" in name:
                full_path = fallback_base / "images" / "blank.jpg"
            else:
                fname = os.path.basename(name)
                full_path = self.stimuli_dir / fname
                if not full_path.exists():
                    full_path = fallback_base / name
            
            if full_path.exists():
                # We only load if the window is already setup (usually it is during setup())
                if hasattr(self, 'window'):
                    self.stim_cache[name] = visual.ImageStim(win=self.window, image=str(full_path), size=(8.4, 8.4), units='deg')
                else:
                    # If called before window setup (unlikely), just store the path
                    self.stim_cache[name] = str(full_path)
            else:
                print(f"  Warning: Image not found: {full_path}")
                
        return list(self.conditions['current_image'].values)

    def present_stimulus(self, idx: int, trial):
        """
        Presents the stimulus for the current trial from cache.
        """
        image_name = self.stim[idx]
        stim_obj = self.stim_cache.get(image_name)
        
        if stim_obj:
            if isinstance(stim_obj, str): # Late binding if not pre-loaded as ImageStim
                stim_obj = visual.ImageStim(win=self.window, image=stim_obj, size=(8.4, 8.4), units='deg')
                self.stim_cache[image_name] = stim_obj
            
            stim_obj.draw()

        # Pushing the sample to the EEG
        if self.eeg:
            timestamp = time()
            # Marker 1 for new, 2 for repeat
            label = int(self.conditions.iloc[idx]['is_repeat']) + 1 
            
            marker = [str(label)] if self.eeg.backend == "muselsl" else label
            self.eeg.push_sample(marker=marker, timestamp=timestamp)
        
        self.window.flip()
