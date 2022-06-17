import os
from time import time
from glob import glob
from random import choice

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event

from eegnb import generate_save_fn
from eegnb.stimuli import CAT_DOG
from eegnb.experiments.Experiment import Experiment

class VisualP300(Experiment):
    
    def __init__(self, duration=120, eeg: EEG=None, save_fn=None,
            n_trials = 2010, iti = 0.4, soa = 0.3, jitter = 0.2):
        
        exp_name = "Visual P300"
        super().__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter)
        
    def load_stimulus(self):
        load_image = lambda fn: visual.ImageStim(win=mywin, image=fn)
        # Setup graphics
        mywin = visual.Window([1600, 900], monitor="testMonitor", units="deg", fullscr=True)
        targets = list(map(load_image, glob(os.path.join(CAT_DOG, "target-*.jpg"))))
        nontargets = list(map(load_image, glob(os.path.join(CAT_DOG, "nontarget-*.jpg"))))
        
        return [nontargets, targets]

    def present_stimulus(self):

        label = self.trials["image_type"].iloc[ii]
        image = choice(targets if label == 1 else nontargets)
        image.draw()

        # Push sample
        if self.eeg:
            timestamp = time()
            if self.eeg.backend == "muselsl":
                marker = [self.markernames[label]]
            else:
                marker = self.markernames[label]
            self.eeg.push_sample(marker=marker, timestamp=timestamp)
