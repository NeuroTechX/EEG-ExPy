""" eeg-notebooks/eegnb/experiments/visual_floc/visual_floc.py """

from time import time
from pathlib import Path
from random import choice
from psychopy import visual
import numpy as np
import pandas as pd
from typing import Optional, List

from eegnb.devices.eeg import EEG
from eegnb.stimuli import FLOC
from eegnb.experiments import Experiment

# Path to the bbfloc stimuli in the workspace
BBFLOC_STIMULI_DIR = Path(FLOC)

class VisualfLoc(Experiment.BaseExperiment):
    """
    fLoc (Functional Localizer) experiment for EEG-ExPy.
    Uses stimuli from the VPNL bbfloc package.
    Optimized for timing by pre-loading images.
    """

    def __init__(self, duration=120, eeg: Optional[EEG]=None, save_fn=None,
                 n_trials=200, iti=0.4, soa=0.3, jitter=0.2, use_vr=False,
                 categories: List[str] = ['faces', 'scenes', 'cars', 'limbs', 'food']):
        
        # Set experiment name
        exp_name = "Visual fLoc"
        self.categories = categories
        
        # Calling the super class constructor
        super(VisualfLoc, self).__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr)

    def load_stimulus(self):
        """
        Loads the stimuli image objects from the bbfloc directory.
        Organizes them by category and pre-loads into ImageStim objects.
        """
        self.stim_cache = {}
        for cat in self.categories:
            files = list(BBFLOC_STIMULI_DIR.glob(f"{cat}-*.jpg"))
            if not files:
                files = list(BBFLOC_STIMULI_DIR.glob(f"{cat}-*.png"))
            
            print(f"Pre-loading {len(files)} images for category: {cat}")
            
            # Pre-load as ImageStim if window exists, else store paths
            if hasattr(self, 'window'):
                self.stim_cache[cat] = [visual.ImageStim(win=self.window, image=str(f), size=(10, 10)) for f in files]
            else:
                self.stim_cache[cat] = [str(f) for f in files]

        return self.categories

    def setup(self, instructions=True):
        # Override setup to ensure window is created before load_stimulus
        self.record_duration = np.float32(self.duration)
        self.markernames = [i + 1 for i in range(len(self.categories))]
        self.parameter = np.random.randint(0, len(self.categories), self.n_trials)
        self.trials = pd.DataFrame(dict(parameter=self.parameter, timestamp=np.zeros(self.n_trials)))

        # Setting up Graphics 
        self.window = (
            visual.Rift(monoscopic=True, headLocked=True) if self.use_vr
            else visual.Window([1600, 900], monitor="testMonitor", units="deg", fullscr=True))
        
        # Load stimulus (now that window is available)
        self.stim = self.load_stimulus()
        
        if instructions:
            self.show_instructions()

        if self.eeg:
            if self.save_fn is None:  
                import random
                from eegnb import generate_save_fn
                random_id = random.randint(1000,10000)
                experiment_directory = self.exp_name.replace(' ', '_')
                self.save_fn = generate_save_fn(self.eeg.device_name, experiment_directory, random_id, random_id, "unnamed")

    def present_stimulus(self, idx: int, trial):
        """
        Presents the stimulus for the current trial.
        """
        # Get the category index
        cat_idx = self.trials["parameter"].iloc[idx]
        category = self.categories[cat_idx]
        
        # Pick a random pre-loaded image from that category
        if self.stim_cache.get(category):
            stim_obj = choice(self.stim_cache[category])
            
            if isinstance(stim_obj, str): # Late binding if setup wasn't called properly
                stim_obj = visual.ImageStim(win=self.window, image=stim_obj, size=(10, 10))
            
            stim_obj.draw()

        # Pushing the sample to the EEG
        if self.eeg:
            timestamp = time()
            marker = self.markernames[cat_idx]
            self.eeg.push_sample(marker=marker, timestamp=timestamp)
        
        self.window.flip()
