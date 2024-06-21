
from eegnb.experiments import Experiment
import os
from time import time
from glob import glob
from random import choice

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event


from eegnb.devices.eeg import EEG
from eegnb import generate_save_fn
from typing import Optional


class VisualSSVEP(Experiment.BaseExperiment):

    def __init__(self, duration=120, eeg: Optional[EEG]=None, save_fn=None, n_trials = 2010, iti = 0.5, soa = 3.0, jitter = 0.2, use_vr=False):
        
        self.use_vr = use_vr
        exp_name = "Visual SSVEP"
        super().__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr)

    def load_stimulus(self):
        
        grating_sf = 400 if self.use_vr else 0.2
        self.grating = visual.GratingStim(win=self.window, mask="circle", size=80, sf=grating_sf)
        self.grating_neg = visual.GratingStim(win=self.window, mask="circle", size=80, sf=grating_sf, phase=0.5)

        self.fixation = visual.GratingStim(win=self.window, pos=[0, 0], sf=grating_sf, color=[1, 0, 0])
        self.fixation.size = 0.02 if self.use_vr else 0.2

        # Generate the possible ssvep frequencies based on monitor refresh rate
        def get_possible_ssvep_freqs(frame_rate, stim_type="single"):
            
            max_period_nb = int(frame_rate / 6)
            periods = np.arange(max_period_nb) + 1
            
            if stim_type == "single":
                freqs = dict()
                for p1 in periods:
                    for p2 in periods:
                        f = frame_rate / (p1 + p2)
                        try:
                            freqs[f].append((p1, p2))
                        except:
                            freqs[f] = [(p1, p2)]

            elif stim_type == "reversal":
                freqs = {frame_rate / p: [(p, p)] for p in periods[::-1]}

            return freqs

        def init_flicker_stim(frame_rate, cycle, soa):
            
            if isinstance(cycle, tuple):
                stim_freq = frame_rate / sum(cycle)
                n_cycles = int(soa * stim_freq)
            
            else:
                stim_freq = frame_rate / cycle
                cycle = (cycle, cycle)
                n_cycles = int(soa * stim_freq) / 2

            return {"cycle": cycle, "freq": stim_freq, "n_cycles": n_cycles}

        # Set up stimuli

        # Frame rate, in Hz
        # GetActualFrameRate() crashes in psychxr due to 'EndFrame called before BeginFrame'
        frame_rate = np.round(self.window.displayRefreshRate if self.use_vr else self.window.getActualFrameRate())
        freqs = get_possible_ssvep_freqs(frame_rate, stim_type="reversal")
        self.stim_patterns = [
        init_flicker_stim(frame_rate, 2, self.soa),
        init_flicker_stim(frame_rate, 3, self.soa),
        ]
        
        print(
            (
                "Flickering frequencies (Hz): {}\n".format(
                    [self.stim_patterns[0]["freq"], self.stim_patterns[1]["freq"]]
                )
            )
        )


        return [
            init_flicker_stim(frame_rate, 2, self.soa),
            init_flicker_stim(frame_rate, 3, self.soa),
        ]

    def present_stimulus(self, idx, trial):
        
        # Select stimulus frequency
        ind = self.trials["parameter"].iloc[idx]

        # Push sample
        if self.eeg:
            timestamp = time()
            if self.eeg.backend == "muselsl":
                marker = [self.markernames[ind]]
            else:
                marker = self.markernames[ind]
            self.eeg.push_sample(marker=marker, timestamp=timestamp)

        # Present flickering stim
        for _ in range(int(self.stim_patterns[ind]["n_cycles"])):

            for _ in range(int(self.stim_patterns[ind]["cycle"][0])):
                if self.use_vr:
                    tracking_state = self.window.getTrackingState()
                    self.window.calcEyePoses(tracking_state.headPose.thePose)
                    self.window.setDefaultView()
                self.grating.draw()
                self.fixation.draw()
                self.window.flip()

            for _ in range(self.stim_patterns[ind]["cycle"][1]):
                if self.use_vr:
                    tracking_state = self.window.getTrackingState()
                    self.window.calcEyePoses(tracking_state.headPose.thePose)
                    self.window.setDefaultView()
                self.grating_neg.draw()
                self.fixation.draw()
                self.window.flip()
        pass