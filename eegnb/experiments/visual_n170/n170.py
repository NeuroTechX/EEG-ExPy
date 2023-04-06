"""  eeg-notebooks/eegnb/experiments/visual_n170/n170.py """

from psychopy import prefs
#change the pref libraty to PTB and set the latency mode to high precision
prefs.hardware['audioLib'] = 'PTB'
prefs.hardware['audioLatencyMode'] = 3

import os
from time import time
from glob import glob
from random import choice
from psychopy import visual, core, event

from eegnb.devices.eeg import EEG
from eegnb.stimuli import FACE_HOUSE
from eegnb.experiments import Experiment
from typing import Optional


class VisualN170(Experiment.BaseExperiment):

    def __init__(self, duration=120, eeg: Optional[EEG]=None, save_fn=None,
            n_trials = 2010, iti = 0.4, soa = 0.3, jitter = 0.2, use_vr=False):

        self.image = None
        # Set experiment name
        exp_name = "Visual N170"
        # Calling the super class constructor to initialize the experiment variables
        super(VisualN170, self).__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr)

    def load_stimulus(self):
        
        # Loading Images from the folder
        load_image = lambda fn: visual.ImageStim(win=self.window, image=fn)

        # Setting up images for the stimulus
        self.faces = list(map(load_image, glob(os.path.join(FACE_HOUSE, "faces", "*_3.jpg"))))
        self.houses = list(map(load_image, glob(os.path.join(FACE_HOUSE, "houses", "*.3.jpg"))))

        # Return the list of images as a stimulus object
        return [self.houses, self.faces]

    # last drawn frame
    rendering_trial = -1

    def present_stimulus(self, current_trial: int):

        # Get the label of the trial
        label = self.trials["parameter"].iloc[current_trial]
        # Get the image to be presented

        # if frame number changed get new choice of image.
        if self.rendering_trial < current_trial:
            self.image = choice(self.faces if label == 1 else self.houses)

        # Redraw/draw the image based on user perspective.
        self.image.draw()

        # If the current frame has not yet been drawn
        if self.rendering_trial < current_trial:
            # Pushing the sample to the EEG
            if 0 < current_trial and self.eeg:
                timestamp = time()
                if self.eeg.backend == "muselsl":
                    marker = [self.markernames[label]]
                else:
                    marker = self.markernames[label]
                self.eeg.push_sample(marker=marker, timestamp=timestamp)

            self.rendering_trial = current_trial
