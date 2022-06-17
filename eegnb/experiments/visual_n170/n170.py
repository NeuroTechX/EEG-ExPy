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
from eegnb.stimuli import FACE_HOUSE
from Experiment import Experiment


def load_stimulus():
    
    load_image = lambda fn: visual.ImageStim(win=mywin, image=fn)
    
    faces = list(map(load_image, glob(os.path.join(FACE_HOUSE, "faces", "*_3.jpg"))))
    houses = list(map(load_image, glob(os.path.join(FACE_HOUSE, "houses", "*.3.jpg"))))

    return [houses, faces]
    
def present_stimulus(trials, ii, eeg, markernames):
   
    label = trials["image_type"].iloc[ii]
    image = choice(faces if label == 1 else houses)
    image.draw()

    # Push sample
    if eeg:
        timestamp = time()
        if eeg.backend == "muselsl":
            marker = [markernames[label]]
        else:
            marker = markernames[label]
        eeg.push_sample(marker=marker, timestamp=timestamp)
   

if __name__ == "__main__":
     
    test = Experiment("Visual N170")
    test.instruction_text = instruction_text
    test.load_stimulus = load_stimulus
    test.present_stimulus = present_stimulus
    test.setup()
    test.present()

