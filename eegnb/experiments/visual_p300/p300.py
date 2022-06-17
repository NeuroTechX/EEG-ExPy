import os
from time import time
from glob import glob
from random import choice

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event

from eegnb import generate_save_fn
from eegnb.stimuli import CAT_DOG


def load_stimulus():
    load_image = lambda fn: visual.ImageStim(win=mywin, image=fn)
    # Setup graphics
    mywin = visual.Window([1600, 900], monitor="testMonitor", units="deg", fullscr=True)
    targets = list(map(load_image, glob(os.path.join(CAT_DOG, "target-*.jpg"))))
    nontargets = list(map(load_image, glob(os.path.join(CAT_DOG, "nontarget-*.jpg"))))
    
    return [nontargets, targets]

def present_stimulus(trials, ii, eeg, markernames):

    label = trials["image_type"].iloc[ii]
    image = choice(targets if label == 1 else nontargets)
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

    test = Experiment("Visual P300")
    test.instruction_text = instruction_text
    test.load_stimulus = load_stimulus
    test.present_stimulus = present_stimulus
    test.setup()
    test.present()
    


