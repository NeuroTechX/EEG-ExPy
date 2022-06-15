import os
from time import time
from glob import glob
from random import choice

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event

from eegnb import generate_save_fn
from Experiment import Experiment


class VisualSSVEP(Experiment):

    def __init__(self, duration=120, eeg: EEG=None, save_fn=None, n_trials = 2010, iti = 0.5, soa = 3.0, jitter = 0.2):
        
        exp_name = "Visual SSVEP"
        super().__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter)

    def load_stimulus(self):
        
        grating = visual.GratingStim(win=mywin, mask="circle", size=80, sf=0.2)
        grating_neg = visual.GratingStim(
            win=mywin, mask="circle", size=80, sf=0.2, phase=0.5
        )
        fixation = visual.GratingStim(
            win=mywin, size=0.2, pos=[0, 0], sf=0.2, color=[1, 0, 0], autoDraw=True
        )

        # Generate the possible ssvep frequencies based on monitor refresh rate
        def get_possible_ssvep_freqs(frame_rate, stim_type="single"):
            if stim_type == "single":
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
        frame_rate = np.round(mywin.getActualFrameRate())  # Frame rate, in Hz
        freqs = get_possible_ssvep_freqs(frame_rate, stim_type="reversal")

        print(
            (
                "Flickering frequencies (Hz): {}\n".format(
                    [stim_patterns[0]["freq"], stim_patterns[1]["freq"]]
                )
            )
        )

        return [
            init_flicker_stim(frame_rate, 2, soa),
            init_flicker_stim(frame_rate, 3, soa),
        ]

    def present_stimulus(self):
        
        # Select stimulus frequency
        ind = self.trials["stim_freq"].iloc[ii]

        # Push sample
        if eeg:
            timestamp = time()
            if self.eeg.backend == "muselsl":
                marker = [self.markernames[ind]]
            else:
                marker = self.markernames[ind]
            self.eeg.push_sample(marker=marker, timestamp=timestamp)

        # Present flickering stim
        for _ in range(int(stim_patterns[ind]["n_cycles"])):
            grating.setAutoDraw(True)
            for _ in range(int(stim_patterns[ind]["cycle"][0])):
                mywin.flip()
            grating.setAutoDraw(False)
            grating_neg.setAutoDraw(True)
            for _ in range(stim_patterns[ind]["cycle"][1]):
                mywin.flip()
            grating_neg.setAutoDraw(False)
        pass
