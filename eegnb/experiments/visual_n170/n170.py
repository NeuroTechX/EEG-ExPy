"""  eeg-notebooks/eegnb/experiments/visual_n170/n170.py """

from psychopy import prefs
#change the pref libraty to PTB and set the latency mode to high precision
prefs.hardware['audioLib'] = 'PTB'
prefs.hardware['audioLatencyMode'] = 3

import os
from time import time
from glob import glob
from random import choice
from optparse import OptionParser
import random

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event

from eegnb.devices.eeg import EEG
from eegnb.stimuli import FACE_HOUSE
from eegnb.experiments import Experiment


class VisualN170(Experiment.BaseExperiment):

    def __init__(self, duration=120, eeg: EEG=None, save_fn=None,
            n_trials = 2010, iti = 0.4, soa = 0.3, jitter = 0.2):
        
        exp_name = "Visual N170"
        super(VisualN170, self).__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter)

    def load_stimulus(self):
        
        load_image = lambda fn: visual.ImageStim(win=self.window, image=fn)
        
        self.faces = list(map(load_image, glob(os.path.join(FACE_HOUSE, "faces", "*_3.jpg"))))
        self.houses = list(map(load_image, glob(os.path.join(FACE_HOUSE, "houses", "*.3.jpg"))))

        return [self.houses, self.faces]
        
    def present_stimulus(self, idx : int):
    
        label = self.trials["parameter"].iloc[idx]
        image = choice(self.faces if label == 1 else self.houses)
        image.draw()

        # Push sample
        if self.eeg:
            timestamp = time()
            if self.eeg.backend == "muselsl":
                marker = [self.markernames[label]]
            else:
                marker = self.markernames[label]
            self.eeg.push_sample(marker=marker, timestamp=timestamp)

        self.window.flip()