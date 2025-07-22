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

        # Set experiment name
        exp_name = "Text N400" # Updated experiment name
        # Call the super class constructor to initialize the experiment variables
        super(TextN400, self).__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter)

        # Define specific marker names for N400 experiment
        # These correspond to the values you'll push to the EEG stream
        self.markernames = {
            'congruent': 1,
            'incongruent': 2
        }

    def load_stimulus(self):
        """
        Loads the text stimuli (congruent and incongruent sentences/words)
        from the specified folders.
        """
        # Define base path for text stimuli
        text_stim_path = N400_TEXT # This points to eegnb/stimuli/text

        # Load congruent words/sentences from text files
        congruent_files = glob(os.path.join(text_stim_path, "congruent", "*.txt"))
        self.congruent_stims = [] # Renamed from words to stims for generality
        for f in congruent_files:
            with open(f, 'r') as file:
                # Assuming each line in the .txt file is one stimulus (word or sentence)
                self.congruent_stims.extend([line.strip() for line in file if line.strip()])

        # Load incongruent words/sentences from text files
        incongruent_files = glob(os.path.join(text_stim_path, "incongruent", "*.txt"))
        self.incongruent_stims = [] # Renamed from words to stims
        for f in incongruent_files:
            with open(f, 'r') as file:
                self.incongruent_stims.extend([line.strip() for line in file if line.strip()])

        # Create a list of trial types and stimuli
        num_congruent = len(self.congruent_stims) # Use actual number of loaded stimuli
        num_incongruent = len(self.incongruent_stims)

        # Determine how many trials of each type based on n_trials parameter, keeping proportions
        total_stims_available = num_congruent + num_incongruent
        if total_stims_available == 0:
            raise ValueError("No stimulus text files found in the congruent or incongruent folders!")

        # Calculate ideal distribution for n_trials, ensuring not to exceed available stimuli
        ratio_congruent = num_congruent / total_stims_available
        ratio_incongruent = num_incongruent / total_stims_available

        trials_to_use_congruent = min(num_congruent, int(self.n_trials * ratio_congruent))
        trials_to_use_incongruent = min(num_incongruent, int(self.n_trials * ratio_incongruent))

        # Adjust total trials if we can't meet n_trials with available unique stimuli
        self.n_trials = trials_to_use_congruent + trials_to_use_incongruent

        # Select stimuli for trials (can use random.sample if no replacement needed, or np.random.choice with replacement)
        selected_congruent = np.random.choice(self.congruent_stims, size=trials_to_use_congruent, replace=True).tolist()
        selected_incongruent = np.random.choice(self.incongruent_stims, size=trials_to_use_incongruent, replace=True).tolist()

        trial_data = []
        for stim_text in selected_congruent:
            trial_data.append({'stim_text': stim_text, 'type': 'congruent'})
        for stim_text in selected_incongruent:
            trial_data.append({'stim_text': stim_text, 'type': 'incongruent'})

        # Shuffle the trials to randomize presentation order
        shuffle(trial_data)

        # Create a pandas DataFrame for easier trial management
        self.trials = pd.DataFrame(trial_data)
        self.trials['iti'] = self.iti + np.random.rand(len(self.trials)) * self.jitter
        self.trials['soa'] = self.soa

        # Setup visual stimulus for text presentation
        # Use visual.TextStim for words/sentences
        self.text_stim = visual.TextStim(win=self.window, text="", color='white', height=0.1) # Initialize with empty text
        self.fixation = visual.GratingStim(win=self.window, size=0.2, pos=[0, 0], sf=0, rgb=[1, 0, 0])
        self.fixation.setAutoDraw(True)

        # Initial flip to show fixation before first trial
        self.window.flip()

        return None

    def present_stimulus(self, idx: int):
        """
        Presents the current word/sentence stimulus and sends a marker to the EEG.
        """
        # Get trial details from the trials DataFrame
        current_trial = self.trials.iloc[idx]
        word_to_display = current_trial['stim_text']
        stim_type = current_trial['type']
        marker_value = self.markernames[stim_type]

        # Update text stimulus and draw it
        self.text_stim.text = word_to_display
        self.text_stim.draw()
        self.fixation.draw() # Ensure fixation is drawn

        # Flip the window to display the word
        self.window.flip()

        # Push the sample to the EEG at the exact moment the word appears
        if self.eeg:
            timestamp = time()
            # Marker value should be an int or a list of ints depending on backend
            marker = [int(marker_value)] if self.eeg.backend == "muselsl" else int(marker_value) # Ensure marker is int
            self.eeg.push_sample(marker=marker, timestamp=timestamp)

        # Wait for the Stimulus Onset Asynchrony (SOA) duration
        core.wait(self.soa)

        # Clear the screen after presentation
        self.text_stim.text = '' # Clear the text
        self.window.flip()

        # Wait for the Inter Trial Interval (ITI) duration before the next trial
        core.wait(current_trial['iti'])