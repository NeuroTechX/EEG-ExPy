""" 
Initial run of the Experiment Class Refactor base class

Specific experiments are implemented as sub classes that overload a load_stimulus and present_stimulus method

Running each experiment:
obj = VisualP300({parameters})
obj.run()
"""

from abc import ABC, abstractmethod
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

from eegnb import generate_save_fn
from eegnb.devices.eeg import EEG

class BaseExperiment:

    def __init__(self, exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter):
        """ Initializer for the Base Experiment Class """

        self.exp_name = exp_name
        self.instruction_text = """\nWelcome to the {} experiment!\nStay still, focus on the centre of the screen, and try not to blink. \nThis block will run for %s seconds.\n
        Press spacebar to continue. \n""".format(self.exp_name)
        self.duration = duration
        self.eeg = eeg
        self.save_fn = save_fn
        self.n_trials = n_trials
        self.iti = iti
        self.soa = soa
        self.jitter = jitter
        
    @abstractmethod
    def load_stimulus(self):
        """ 
        Method that loads the stimulus for the specific experiment, overwritten by the specific experiment
        Returns the stimulus object in the form of [{stim1},{stim2},...]
        Throws error if not overwritten in the specific experiment
        """
        raise NotImplementedError

    @abstractmethod
    def present_stimulus(self, idx : int):
        """
        Method that presents the stimulus for the specific experiment, overwritten by the specific experiment
        Displays the stimulus on the screen
        Pushes EEG Sample if EEG is enabled
        Throws error if not overwritten in the specific experiment

        idx : Trial index for the current trial
        """
        raise NotImplementedError

    def setup(self, instructions=True):

        # Initializing the record duration and the marker names
        self.record_duration = np.float32(self.duration)
        self.markernames = [1, 2]
        
        # Setting up the trial and parameter list
        self.parameter = np.random.binomial(1, 0.5, self.n_trials)
        self.trials = DataFrame(dict(parameter=self.parameter, timestamp=np.zeros(self.n_trials)))

        # Setting up Graphics 
        self.window = visual.Window([1600, 900], monitor="testMonitor", units="deg", fullscr=True) 
        
        # Loading the stimulus from the specific experiment, throws an error if not overwritten in the specific experiment
        self.stim = self.load_stimulus()
        
        # Show Instruction Screen if not skipped by the user
        if instructions:
            self.show_instructions()

        # Checking for EEG to setup the EEG stream
        if self.eeg:
             # If no save_fn passed, generate a new unnamed save file
            if self.save_fn is None:  
                # Generating a random int for the filename
                random_id = random.randint(1000,10000)
                # Generating save function
                self.save_fn = generate_save_fn(self.eeg.device_name, "visual_n170", random_id, random_id, "unnamed")
                print(
                    f"No path for a save file was passed to the experiment. Saving data to {self.save_fn}"
                )
    
    def show_instructions(self):
        """ 
        Method that shows the instructions for the specific Experiment
        In the usual case it is not overwritten, the instruction text can be overwritten by the specific experiment
        No parameters accepted, can be skipped through passing a False while running the Experiment
        """

        # Splitting instruction text into lines
        self.instruction_text = self.instruction_text % self.duration

        # Disabling the cursor during display of instructions
        self.window.mouseVisible = False

        # Displaying the instructions on the screen
        text = visual.TextStim(win=self.window, text=self.instruction_text, color=[-1, -1, -1])
        text.draw()
        self.window.flip()
        
        # Waiting for the user to press the spacebar to start the experiment
        event.waitKeys(keyList="space")

        # Enabling the cursor again
        self.window.mouseVisible = True
       
    def run(self, instructions=True):
        """ Do the present operation for a bunch of experiments """

        # Setup the experiment, alternatively could get rid of this line, something to think about
        self.setup(instructions)
    
        # Start EEG Stream, wait for signal to settle, and then pull timestamp for start point
        if self.eeg:
            self.eeg.start(self.save_fn, duration=self.record_duration + 5)

        start = time()
        
        # Iterate through the events
        for ii, trial in self.trials.iterrows():
          
            # Intertrial interval
            core.wait(self.iti + np.random.rand() * self.jitter)

            # Stimulus presentation overwritten by specific experiment
            self.present_stimulus(ii)

            # Offset
            core.wait(self.soa)
            self.window.flip()

            # Exiting the loop condition, looks ugly and needs to be fixed
            if len(event.getKeys()) > 0 or (time() - start) > self.record_duration:
                break

            # Clearing the screen for the next trial    
            event.clearEvents()
        
        # Closing the EEG stream 
        if self.eeg:
            self.eeg.stop()

        # Closing the window
        self.window.close()

    
    