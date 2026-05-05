""" eeg-notebooks/eegnb/experiments/visual_natural_prf/natural_prf.py """

from pathlib import Path
from random import choice
from time import time
from typing import Optional

import numpy as np
from psychopy import core, visual

from eegnb.devices.eeg import EEG
from eegnb.experiments import Experiment
from eegnb.stimuli import MINDEYE_STIMULI


class VisualNaturalPRF(Experiment.BaseExperiment):
    """
    Naturalistic pRF Mapping experiment for EEG-ExPy.
    Uses drifting bars with flickering natural images (MindEye stimuli).
    Based on the Kendrick Kay / HCP protocol.
    """

    def __init__(self, duration=300, eeg: Optional[EEG]=None, save_fn=None,
                 n_trials=None, iti=0.0, soa=0.5, jitter=0.0, use_vr=False,
                 bar_width=2.5, sweep_steps=20, stimuli_dir=None):

        exp_name = "Naturalistic pRF"
        self.bar_width = bar_width
        self.sweep_steps = sweep_steps
        self.stimuli_dir = Path(stimuli_dir) if stimuli_dir else MINDEYE_STIMULI

        if n_trials is None:
            n_trials = int(duration / soa)

        super(VisualNaturalPRF, self).__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr)

    def load_stimulus(self):
        """
        Loads MindEye stimuli to use as carrier patterns.
        """
        if not self.stimuli_dir.exists():
            print(f"Warning: Stimuli directory not found at {self.stimuli_dir}")
            self.image_files = []
        else:
            self.image_files = list(self.stimuli_dir.glob("*.jpg"))
            print(f"Loaded {len(self.image_files)} images for pRF carrier.")

        # Create the masking bar
        self.carrier = visual.ImageStim(win=self.window, size=(20, 20))
        self.fixation = visual.GratingStim(win=self.window, size=0.2, pos=[0,0], sf=0, color=[1, 0, 0])

        return [self.carrier]

    def present_stimulus(self, idx: int, trial):
        """
        Presents one step of the bar sweep with flickering natural images.
        """
        cycle_len = self.sweep_steps
        step_in_cycle = idx % cycle_len
        direction = (idx // cycle_len) % 4

        pos_range = np.linspace(-10, 10, cycle_len)
        pos = pos_range[step_in_cycle]

        # Define aperture bounds in degrees
        if direction == 0: # L-R
            rect = [pos - self.bar_width/2, -10, pos + self.bar_width/2, 10]
        elif direction == 1: # R-L
            rect = [-pos - self.bar_width/2, -10, -pos + self.bar_width/2, 10]
        elif direction == 2: # U-D
            rect = [-10, -pos - self.bar_width/2, 10, -pos + self.bar_width/2]
        else: # D-U
            rect = [-10, pos - self.bar_width/2, 10, pos + self.bar_width/2]

        # Flicker carrier images at 15Hz (approx)
        flicker_period = 1.0 / 15.0
        start_time = core.getTime()

        mask_bar = visual.Rect(win=self.window, size=(self.bar_width, 20), pos=(0,0), fillColor='white')
        if direction < 2:
            mask_bar.pos = [rect[0] + self.bar_width/2, 0]
            mask_bar.size = [self.bar_width, 20]
        else:
            mask_bar.pos = [0, rect[1] + self.bar_width/2]
            mask_bar.size = [20, self.bar_width]

        while core.getTime() - start_time < self.soa:
            # Update carrier image
            if self.image_files:
                self.carrier.image = str(choice(self.image_files))

            # Draw
            self.carrier.draw()
            self.fixation.draw()
            self.window.flip()
            core.wait(flicker_period)

        if self.eeg:
            self.eeg.push_sample(marker=300 + direction, timestamp=time())
