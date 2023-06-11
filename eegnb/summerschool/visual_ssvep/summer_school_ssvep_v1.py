
#from eegnb.experiments import Experiment
from eegnb.summerschool import Experiment_modified as Experiment
import os
from time import time
from glob import glob
from random import choice

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event


from eegnb.devices.eeg import EEG
from eegnb import generate_save_fn
from eegnb.stimuli import SUMMER_SCHOOL

ITI=0.4
SOA=1
JITTER=0.2
NTRIALS=2010
STI_LOC_WIDTH=10
STI_LOC_HEIGHT=0

BACKGROUND_COLOR=[1,0.6,0.6]
FIXATION_COLOR=[1, 0, 0]
"""
[1,1,1] is white
[0,0,0] is grey
[-1,-1,-1] is black
[1.0,-1,-1] is red
[1.0,0.6,0.6] is pink
"""
STI_CHOICE=1 # 0 for the original gratings, 1 for the pictures specified below
IMG_DISPLAY_SIZE=[10,10] #  width, height
FOLDER1='houses'
PHOTOEXT1='*.jpg'
FOLDER2='mountains'
PHOTOEXT2='*.png'

T_ARROW=1
Introduction_msg = """\nWelcome to the SSVEP experiment!\nStay still, focus on the stimuli, and try not to blink. \nThis block will run for %s seconds.\n
        Press spacebar to continue and c to terminate. \n"""

class Summer_School_VisualSSVEP_dual(Experiment.BaseExperiment):

    def __init__(self, duration=120, eeg: EEG=None, save_fn=None, n_trials = NTRIALS, iti = ITI, soa = 0, jitter = JITTER):
        
        exp_name = "Visual SSVEP"
        self.grating_size = [40, 10]
        
        super().__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, default_color=BACKGROUND_COLOR)

    def load_stimulus_img(self):
        
        # Loading Images from the folder
        load_image = lambda fn: visual.ImageStim(win=self.window, image=fn, size=IMG_DISPLAY_SIZE)

        # Setting up images for the stimulus
        self.scene1 = list(map(load_image, glob(os.path.join(SUMMER_SCHOOL, FOLDER1, PHOTOEXT1)))) # face
        
        self.scene2 = list(map(load_image, glob(os.path.join(SUMMER_SCHOOL, FOLDER2, PHOTOEXT2)))) # house

        
    def load_stimulus(self):
        self.load_stimulus_img()

        #grating_size = [40, 10]
        #self.grating = visual.GratingStim(win=self.window, mask="circle", size=80, sf=0.2)
        self.grating = visual.GratingStim(win=self.window, mask="sqr", size=self.grating_size, sf=0.2, pos=(STI_LOC_WIDTH, STI_LOC_HEIGHT))
        
        #self.grating_neg = visual.GratingStim(win=self.window, mask="circle", size=80, sf=0.2, phase=0.5)
        self.grating_neg = visual.GratingStim(win=self.window, mask="sqr", size=self.grating_size, sf=0.2, phase=0.5, pos=(STI_LOC_WIDTH, STI_LOC_HEIGHT))

        fixation = visual.GratingStim(win=self.window, size=0.2, pos=[0, 0], sf=0.2, color=FIXATION_COLOR, autoDraw=True)

        
        # Generate the possible ssvep frequencies based on monitor refresh rate
        def get_possible_ssvep_freqs(frame_rate, stim_type="single"):
            
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

        # Set up stimuli, 7.5Hz (1:1), 12Hz (1:1)
        frame_rate = np.round(self.window.getActualFrameRate())  # Frame rate, in Hz
        self.frame_rate = frame_rate
        freqs = get_possible_ssvep_freqs(frame_rate, stim_type="reversal")
        self.stim_patterns = [
        init_flicker_stim(frame_rate, int(frame_rate/7.5), self.soa), # 2
        init_flicker_stim(frame_rate, int(frame_rate/12), self.soa), # 3
        ]
        
        print(
            (
                "Flickering frequencies (Hz): {}\n".format(
                    [self.stim_patterns[0]["freq"], self.stim_patterns[1]["freq"]]
                )
            )
        )

        return [
            init_flicker_stim(frame_rate, int(frame_rate/7.5), self.soa),
            init_flicker_stim(frame_rate, int(frame_rate/12), self.soa),
        ]


    def present_stimulus(self, idx, trial): # 2 flickr
        #self.window.color = BACKGROUND_COLOR
        # Select stimulus frequency
        ind = self.trials["parameter"].iloc[idx]

        # Push sample
        if self.eeg:
            timestamp = time()
            if self.eeg.backend == "muselsl":
                marker = [self.markernames[ind]]
            else:
                marker = self.markernames[ind]
            self.eeg.push_sample(marker=marker, timestamp=timestamp)

        
        # select the position of 7.5 Hz flickr
        flk_pos = choice([0,1])
        flk_sti = choice([0,1])

        
        mylist = [STI_LOC_WIDTH,-STI_LOC_WIDTH]
        if STI_CHOICE == 0:
            gratinglist = [self.grating, self.grating_neg]
        else:
            # image
            gratinglist = [choice(self.scene1), choice(self.scene2)]
        
        # Present flickering stim
        # https://stackoverflow.com/questions/37469796/where-can-i-find-flickering-functions-for-stimuli-on-psychopy-and-how-do-i-use
        #for _ in range(int(self.stim_patterns[ind]["n_cycles"])):
        current_frame = 0
        grating_choice = gratinglist[flk_sti]
        grating_choice.pos = (mylist[flk_pos], STI_LOC_HEIGHT)

        

        # [7.5, 12]
        flicker_frequency = 7.5
        
        grating_choice.setAutoDraw(False)
        
        for _ in range(int(SOA * self.frame_rate) ): #range(int(self.stim_patterns[ind]["cycle"][0])):
            if current_frame % (2*flicker_frequency) < flicker_frequency:
                #self.window.flip()
                grating_choice.draw()
            
            self.window.flip()
            current_frame += 1  # increment by 1.
        #grating_choice.setAutoDraw(False)
        self.random_record = [arr_choice, flk_pos, flk_sti]

    def present_stimulus_1flickr(self, idx, trial): # 1 flickr
        
        # Select stimulus frequency
        ind = self.trials["parameter"].iloc[idx]

        # Push sample
        if self.eeg:
            timestamp = time()
            if self.eeg.backend == "muselsl":
                marker = [self.markernames[ind]]
            else:
                marker = self.markernames[ind]
            self.eeg.push_sample(marker=marker, timestamp=timestamp)

        mylist = [15,-15]
        gratinglist = [self.grating, self.grating_neg]
        
        # Present flickering stim
        # https://stackoverflow.com/questions/37469796/where-can-i-find-flickering-functions-for-stimuli-on-psychopy-and-how-do-i-use
        #for _ in range(int(self.stim_patterns[ind]["n_cycles"])):
        current_frame = 0
        grating_choice = choice(gratinglist)
        grating_choice.pos = (choice(mylist), 0)
        flicker_frequency = choice([7.5, 12])

        grating_choice.setAutoDraw(False)
        for _ in range(int(SOA * self.frame_rate) ): #range(int(self.stim_patterns[ind]["cycle"][0])):
            if current_frame % (2*flicker_frequency) < flicker_frequency:
                #self.window.flip()
                grating_choice.draw()
            self.window.flip()
            current_frame += 1  # increment by 1.
        #grating_choice.setAutoDraw(False)

        
    
    
    