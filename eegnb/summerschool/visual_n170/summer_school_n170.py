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
from eegnb.stimuli import SUMMER_SCHOOL # FACE_HOUSE
#from eegnb.experiments import Experiment_modified as Experiment
from eegnb.summerschool import Experiment_modified as Experiment

ITI=0.4
SOA=0.3 # 0.3 image show time
FOLDER1='houses'
PHOTOEXT1='*.jpg'
FOLDER2='mountains'
PHOTOEXT2='*.png'
BACKGROUND_COLOR=[-1,-1,-1]
JITTER=0.2
NTRIALS=2010

class Summer_School_VisualN170(Experiment.BaseExperiment):

    def __init__(self, duration=120, eeg: EEG=None, save_fn=None,
            n_trials = NTRIALS, iti = ITI, soa = SOA, jitter = JITTER):

        # Set experiment name        
        exp_name = "Visual N170 modified"
        # Calling the super class constructor to initialize the experiment variables
        super(Summer_School_VisualN170, self).__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, default_color=BACKGROUND_COLOR)

    def load_stimulus(self):
        
        # Loading Images from the folder
        load_image = lambda fn: visual.ImageStim(win=self.window, image=fn)

        # Setting up images for the stimulus
        self.scene1 = list(map(load_image, glob(os.path.join(SUMMER_SCHOOL, FOLDER1, PHOTOEXT1)))) # face
        
        self.scene2 = list(map(load_image, glob(os.path.join(SUMMER_SCHOOL, FOLDER2, PHOTOEXT2)))) # house

        # Return the list of images as a stimulus object
        return [self.scene1, self.scene2]
        
    def present_stimulus(self, idx : int, trial):
        
        # Get the label of the trial
        label = self.trials["parameter"].iloc[idx]
        # Get the image to be presented
        image = choice(self.scene1 if label == 1 else self.scene2)
        # Draw the image
        image.draw()

        # Pushing the sample to the EEG
        if self.eeg:
            timestamp = time()
            if self.eeg.backend == "muselsl":
                marker = [self.markernames[label]]
            else:
                marker = self.markernames[label]
            self.eeg.push_sample(marker=marker, timestamp=timestamp)
        
        self.window.flip()

        return []

if __name__ == "__main__":
    module = Summer_School_VisualN170()
    module.__init__()