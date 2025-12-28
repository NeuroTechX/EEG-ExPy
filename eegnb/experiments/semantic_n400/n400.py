""" eeg-notebooks/eegnb/experiments/semantic_n400/n400.py """

import os
from time import time
from glob import glob
from random import choice, shuffle
from psychopy import visual, core, event

from eegnb.devices.eeg import EEG
from eegnb.stimuli import N400_TEXT
from eegnb.experiments import Experiment
from typing import Optional

import pandas as pd
import numpy as np


class TextN400(Experiment.BaseExperiment):

    def __init__(self, duration=120, eeg: Optional[EEG]=None, save_fn=None,
            n_trials=200, iti=0.5, soa=0.5, jitter=0.2):

        
        exp_name = "Text N400" 
        
        super(TextN400, self).__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter)

        
        
        self.markernames = {
            'congruent': 1,
            'incongruent': 2
        }

    def load_stimulus(self):
        """
        Loads the text stimuli (congruent and incongruent sentences/words)
        from the specified folders.
        """
        
        text_stim_path = N400_TEXT 

        
        congruent_files = glob(os.path.join(text_stim_path, "congruent", "*.txt"))
        self.congruent_stims = [] 
        for f in congruent_files:
            with open(f, 'r') as file:
                
                self.congruent_stims.extend([line.strip() for line in file if line.strip()])

        
        incongruent_files = glob(os.path.join(text_stim_path, "incongruent", "*.txt"))
        self.incongruent_stims = [] 
        for f in incongruent_files:
            with open(f, 'r') as file:
                self.incongruent_stims.extend([line.strip() for line in file if line.strip()])

        
        num_congruent = len(self.congruent_stims) 
        num_incongruent = len(self.incongruent_stims)

        
        total_stims_available = num_congruent + num_incongruent
        if total_stims_available == 0:
            raise ValueError("No stimulus text files found in the congruent or incongruent folders!")

        
        ratio_congruent = num_congruent / total_stims_available
        ratio_incongruent = num_incongruent / total_stims_available

        trials_to_use_congruent = min(num_congruent, int(self.n_trials * ratio_congruent))
        trials_to_use_incongruent = min(num_incongruent, int(self.n_trials * ratio_incongruent))

        
        self.n_trials = trials_to_use_congruent + trials_to_use_incongruent

        
        selected_congruent = np.random.choice(self.congruent_stims, size=trials_to_use_congruent, replace=True).tolist()
        selected_incongruent = np.random.choice(self.incongruent_stims, size=trials_to_use_incongruent, replace=True).tolist()

        trial_data = []
        for stim_text in selected_congruent:
            trial_data.append({'stim_text': stim_text, 'type': 'congruent'})
        for stim_text in selected_incongruent:
            trial_data.append({'stim_text': stim_text, 'type': 'incongruent'})

        
        shuffle(trial_data)

        
        self.trials = pd.DataFrame(trial_data)
        self.trials['iti'] = self.iti + np.random.rand(len(self.trials)) * self.jitter
        self.trials['soa'] = self.soa

        
        
        self.text_stim = visual.TextStim(win=self.window, text="", color='white', height=0.1) 
        self.fixation = visual.GratingStim(win=self.window, size=0.2, pos=[0, 0], sf=0, rgb=[1, 0, 0])
        self.fixation.setAutoDraw(True)

        
        self.window.flip()

        return None

    def present_stimulus(self, idx: int):
        """
        Presents the current word/sentence stimulus and sends a marker to the EEG.
        """
        
        current_trial = self.trials.iloc[idx]
        word_to_display = current_trial['stim_text']
        stim_type = current_trial['type']
        marker_value = self.markernames[stim_type]

        
        self.text_stim.text = word_to_display
        self.text_stim.draw()
        self.fixation.draw() 

        
        self.window.flip()

        
        if self.eeg:
            timestamp = time()
            
            marker = [int(marker_value)] if self.eeg.backend == "muselsl" else int(marker_value) 
            self.eeg.push_sample(marker=marker, timestamp=timestamp)

        
        core.wait(self.soa)

        
        self.text_stim.text = '' 
        self.window.flip()

        
        core.wait(current_trial['iti'])