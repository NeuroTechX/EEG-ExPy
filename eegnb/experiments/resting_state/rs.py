"""  eeg-notebooks/eegnb/experiments/resting_state/rs.py """

from eegnb.experiments import Experiment
import os
from time import time
from glob import glob
from random import choice

import numpy as np
from pandas import DataFrame
from psychopy import visual, sound, core, event

from eegnb.devices.eeg import EEG
from eegnb import generate_save_fn
from typing import Optional

class RestingState(Experiment.BaseExperiment):
    """Resting State (Eyes Open / Eyes Closed) Experiment

    Args:
        Experiment (Experiment.BaseExperiment): Base Experiment Class
    
    Options:
        duration: duration of the recording in seconds. default 300
        eeg [Optional]: EEG device object. default None
        save_fn [Optional]: function to save the data. default None
        iti: intertrial interval. default 30
        lf_tone: tone frequency for low-frequency stimulus > EC. default 400
        hf_tone: tone frequency for high-frequency stimulus > EO. default 800
        tone_length: length of each beep. default 0.2
    """

    def __init__(self, duration=300,
                 eeg: Optional[EEG]=None,
                 save_fn=None,
                 iti=0.4,          # default values - off of n170
                 soa=0.3,          # stimulus onset asyncronicity. default values - off of n170
                 jitter = 0,       # jitter in the intertrial intervals
                 lf_tone=400,      # tone frequency for low-frequency stimulus > EC
                 hf_tone=800,      # tone frequency for high-frequency stimulus > EO
                 epoch_length = 5, # length of each eyes open / eyes closed block
                 tone_length = 0.2 # length of each beep
                 ):
        
        exp_name = "Resting State (Eyes Open / Eyes Closed)"
        n_trials = int(duration // iti)

        super().__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter)
        self.lf_tone = lf_tone
        self.hf_tone = hf_tone
        self.tone_length = tone_length
        self.total_duration = duration
        self.epoch_length = epoch_length

    def load_stimulus(self):
        """ loads the stimuli for the experiment
        """
        # self.eyes_open_tone = sound.Sound(value=self.lf_tone, secs=self.tone_length)
        # self.eyes_closed_tone = sound.Sound(value=self.hf_tone, secs=self.tone_length)
        # return [self.eyes_open_tone, self.eyes_closed_tone]

    def present_stimulus(self, idx=None, trial=None):
        """ presents the stimulus
        """

    def run_rs(self):
        # PsychoPy essentials
        self.window = visual.Window([800, 600], fullscr=True)
        self.start_time = core.getTime()
        self.message = visual.TextStim(self.window, text='Welcome to the Resting State (Eyes Open / Eyes Closed) Experiment!\n\nStay still, focus on the centre of the screen, and try not to blink.\n\nThis block will run for %s seconds.\n\nPress spacebar to continue.' % self.total_duration, color='black')

        # Wait for the spacebar press to go on
        self.message.draw()
        self.window.flip()
        event.waitKeys(keyList='space')

        # sounds to play:
        self.eyes_open_tone = sound.Sound(value=self.hf_tone, secs=self.tone_length)
        self.eyes_closed_tone = sound.Sound(value=self.lf_tone, secs=self.tone_length)

        while core.getTime() - self.start_time < self.total_duration:
            epoch_index = int((core.getTime() - self.start_time) // self.epoch_length)
            eyes_open = epoch_index % 2 == 0

            if eyes_open:
                self.eyes_open_tone.play()
                self.message.text = 'Eyes Open'
            else:
                self.eyes_closed_tone.play()
                self.message.text = 'Eyes Closed'

            self.message.draw()
            self.window.flip()

            # Wait for the duration of the epoch
            core.wait(self.epoch_length - self.tone_length)

            # Check for quit key
            if 'escape' in event.getKeys():
                break

        self.window.close()
        core.quit()
