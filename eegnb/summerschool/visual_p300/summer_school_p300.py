
"""  eeg-notebooks/eegnb/experiments/visual_p300/p300.py """

import os
from time import time
from glob import glob
from random import choice
from optparse import OptionParser
import random

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event

from eegnb.stimuli import CAT_DOG
#from eegnb.experiments import Experiment
from eegnb.summerschool import Experiment_modified as Experiment
from eegnb.devices.eeg import EEG

ITI=0.4
SOA=0.3 # 0.3 image show time
JITTER=0.2
NTRIALS=2010

IMG_FOLDER=CAT_DOG
TARGET_FILE="target-*.jpg"
NONTARGET_FILE="nontarget-*.jpg"

class Summer_School_VisualP300(Experiment.BaseExperiment):
    
    def __init__(self, duration=120, eeg: EEG=None, save_fn=None,
            n_trials = NTRIALS, iti = ITI, soa = SOA, jitter = JITTER):
        
        exp_name = "Visual P300"
        super().__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter)
        
    def load_stimulus(self):
        
        load_image = lambda fn: visual.ImageStim(win=self.window, image=fn)
        
        self.targets = list(map(load_image, glob(os.path.join(IMG_FOLDER, TARGET_FILE))))
        self.nontargets = list(map(load_image, glob(os.path.join(IMG_FOLDER, NONTARGET_FILE))))
        
        return [self.nontargets, self.targets]

    def present_stimulus(self, idx:int, trial):

        label = self.trials["parameter"].iloc[idx]
        image = choice(self.targets if label == 1 else self.nontargets)
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