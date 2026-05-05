""" eeg-notebooks/eegnb/experiments/visual_retinotopy/visual_retinotopy.py """

from time import time
from typing import Optional

import numpy as np
from psychopy import core, visual

from eegnb.devices.eeg import EEG
from eegnb.experiments import Experiment


class VisualRetinotopy(Experiment.BaseExperiment):
    """
    Retinotopic Mapping experiment for EEG-ExPy.
    Implements drifting bar, expanding ring, and rotating wedge stimuli
    (Wandell-style) using PsychoPy.
    """

    def __init__(self, duration=120, eeg: Optional[EEG]=None, save_fn=None,
                 n_trials=None, iti=0.0, soa=1.0, jitter=0.0, use_vr=False,
                 stim_type='bars', bar_width=2.5, sweep_steps=20):

        exp_name = f"Visual Retinotopy ({stim_type})"
        self.stim_type = stim_type
        self.bar_width = bar_width
        self.sweep_steps = sweep_steps

        if n_trials is None:
            n_trials = int(duration / soa)

        super(VisualRetinotopy, self).__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr)

    def load_stimulus(self):
        """
        Initializes the retinotopic stimuli.
        """
        if self.stim_type == 'bars':
            self.stim_obj = visual.GratingStim(win=self.window, mask="rect", size=(self.bar_width, 20),
                                              sf=0.5, tex="sqr", color=[1, 1, 1])
        elif self.stim_type == 'rings':
            # Expanding ring using an annular mask
            self.stim_obj = visual.GratingStim(win=self.window, mask="raisedCos", size=(20, 20),
                                              sf=0.5, tex="sqr", color=[1, 1, 1])
        elif self.stim_type == 'wedges':
            # Rotating wedge
            self.stim_obj = visual.RadialStim(win=self.window, tex='sqr', color=[1,1,1], size=(20, 20),
                                             angularRes=360, radialRes=1, angularCycles=8)

        self.fixation = visual.GratingStim(win=self.window, size=0.2, pos=[0,0], sf=0, color=[1, 0, 0])
        return [self.stim_obj]

    def present_stimulus(self, idx: int, trial):
        """
        Presents one step of the retinotopic sweep.
        """
        cycle_len = self.sweep_steps
        step_in_cycle = idx % cycle_len

        if self.stim_type == 'bars':
            direction = (idx // cycle_len) % 4
            pos_range = np.linspace(-10, 10, cycle_len)
            pos = pos_range[step_in_cycle]
            if direction == 0: self.stim_obj.pos, self.stim_obj.ori, self.stim_obj.size = [pos, 0], 0, [self.bar_width, 20]
            elif direction == 1: self.stim_obj.pos, self.stim_obj.ori, self.stim_obj.size = [-pos, 0], 0, [self.bar_width, 20]
            elif direction == 2: self.stim_obj.pos, self.stim_obj.ori, self.stim_obj.size = [0, -pos], 90, [self.bar_width, 20]
            else: self.stim_obj.pos, self.stim_obj.ori, self.stim_obj.size = [0, pos], 90, [self.bar_width, 20]
            marker = 100 + direction

        elif self.stim_type == 'rings':
            # Expanding ring: change size or radial frequency
            radius = np.linspace(0.1, 15, cycle_len)[step_in_cycle]
            self.stim_obj.size = (radius, radius)
            marker = 200

        elif self.stim_type == 'wedges':
            # Rotating wedge: change orientation
            angle = np.linspace(0, 360, cycle_len)[step_in_cycle]
            self.stim_obj.ori = angle
            marker = 300

        # Flicker and Flip
        flicker_freq = 8
        start_time = core.getTime()
        while core.getTime() - start_time < self.soa:
            self.stim_obj.phase = np.floor((core.getTime() - start_time) * flicker_freq * 2) / 2.0
            self.stim_obj.draw()
            self.fixation.draw()
            self.window.flip()

        if self.eeg:
            self.eeg.push_sample(marker=marker, timestamp=time())
