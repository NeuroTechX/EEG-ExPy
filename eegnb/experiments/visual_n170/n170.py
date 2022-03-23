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
from eegnb.devices.fnirs import FNIRS
from eegnb.stimuli import FACE_HOUSE

__title__ = "Visual N170"


def present(duration=120, eeg: EEG=None, fnirs: FNIRS=None, save_fn=None):
    n_trials = 2010
    iti = 0.4
    soa = 0.3
    jitter = 0.2
    record_duration = np.float32(duration)
    markernames = [1, 2]

    # Setup trial list
    image_type = np.random.binomial(1, 0.5, n_trials)
    trials = DataFrame(dict(image_type=image_type, timestamp=np.zeros(n_trials)))

    def load_image(fn):
        return visual.ImageStim(win=mywin, image=fn)

    # start the EEG stream, will delay 5 seconds to let signal settle

    # Setup graphics
    mywin = visual.Window([1600, 900], monitor="testMonitor", units="deg", fullscr=True)

    faces = list(map(load_image, glob(os.path.join(FACE_HOUSE, "faces", "*_3.jpg"))))
    houses = list(map(load_image, glob(os.path.join(FACE_HOUSE, "houses", "*.3.jpg"))))
    stim = [houses, faces]

    if eeg:
        if save_fn is None:  # If no save_fn passed, generate a new unnamed save file
            random_id = random.randint(1000,10000)
            save_fn = generate_save_fn(eeg.device_name, "visual_n170", random_id, random_id, "unnamed")
            print(
                f"No path for a save file was passed to the experiment. Saving data to {save_fn}"
            )
        eeg.start(save_fn, duration=record_duration + 5)


    # start the fNIRS device
    if fnirs:
        fnirs.start()#save_fn, duration=record_duration)


    # Show the instructions screen
    show_instructions(duration)

    # Start EEG Stream, wait for signal to settle, and then pull timestamp for start point
    start = time()

    # Iterate through the events
    for ii, trial in trials.iterrows():
        # Inter trial interval
        core.wait(iti + np.random.rand() * jitter)

        # Select and display image
        label = trials["image_type"].iloc[ii]
        image = choice(faces if label == 1 else houses)
        image.draw()


        # Push triggers

        marker = markernames[label]
        if marker == 1:
            marker_name = 'face'
        elif marker == 2:
            marker_name = 'house'


        timestamp = time()
        if eeg:
            if eeg.backend == "muselsl":
                #marker = [additional_labels["labels"][iteratorthing - 1]]
                #eeg_marker = [marker]
                eeg_marker=[markernames[label]]
                eeg_marker = list(map(int, eeg_marker))
            else:
                #eeg_marker = marker # additional_labels["labels"][iteratorthing - 1]\
                #eeg_marker = markernames[label]
                eeg_marker = marker
            eeg.push_sample(marker=eeg_marker, timestamp=timestamp)

        if fnirs:
            marker_name = 'event_' + marker_name
            fnirs.push_sample(timestamp=timestamp, marker=marker,marker_name=marker_name)



        mywin.flip()

        #offset
        core.wait(soa)
        mywin.flip()
        if len(event.getKeys()) > 0:
            break
        if (time() - start) > record_duration:
            break
        event.clearEvents()



    # Cleanup
    if eeg:
        eeg.stop()

    if fnirs:
        fnirs.stop()


    mywin.close()







def show_instructions(duration):

    instruction_text = """
    Welcome to the N170 experiment! 
 
    Stay still, focus on the centre of the screen, and try not to blink. 

    This block will run for %s seconds.

    Press spacebar to continue. 
    
    """
    instruction_text = instruction_text % duration

    # graphics
    mywin = visual.Window([1600, 900], monitor="testMonitor", units="deg", fullscr=True)

    mywin.mouseVisible = False

    # Instructions
    text = visual.TextStim(win=mywin, text=instruction_text, color=[-1, -1, -1])
    text.draw()
    mywin.flip()
    event.waitKeys(keyList="space")

    mywin.mouseVisible = True
    mywin.close()
