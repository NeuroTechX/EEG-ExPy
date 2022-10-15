from psychopy import prefs
#change the pref libraty to PTB and set the latency mode to high precision
prefs.hardware['audioLib'] = 'PTB'
prefs.hardware['audioLatencyMode'] = 3

import os
from time import time
from glob import glob
import random

import numpy as np
from psychopy import visual, event

from eegnb import generate_save_fn
from eegnb.devices.eeg import EEG
from eegnb.stimuli import PATTERN_REVERSAL

__title__ = "Visual P100"


def present(duration=120, eeg: EEG=None, save_fn=None, use_rift=False):
    experiment_name = "visual_p100_both_eyes"
    frame_duration_seconds = 0.5
    record_duration = np.float32(duration)
    markernames = [1, 2]

    def load_image(fn):
        return visual.ImageStim(win=mywin, image=fn)

    # Setup graphics
    mywin = visual.Rift(monoscopic=True, headLocked=False) if use_rift else visual.Window([1600, 900], monitor="testMonitor", units="deg", fullscr=True)

    checkerboard = list(map(load_image, glob(os.path.join(PATTERN_REVERSAL, "checker*.jpeg"))))

    # Show the instructions screen
    show_instructions(mywin, duration)

    # Start EEG Stream, wait for signal to settle for five seconds, and then pull timestamp for start point
    if eeg:
        if save_fn is None:  # If no save_fn passed, generate a new unnamed save file
            random_id = random.randint(1000,10000)
            save_fn = generate_save_fn(eeg.device_name, experiment_name, random_id, random_id, "unnamed")
            print(
                f"No path for a save file was passed to the experiment. Saving data to {save_fn}"
            )
        eeg.start(save_fn, duration=record_duration + 5)
    start = time()

    def draw():
        image.draw()

    drawn_frame = -1
    checkerboard_frame = 0
    stopDrawing = False
    while not stopDrawing:
        current_interval_seconds = time() - start
        current_frame = int(current_interval_seconds // frame_duration_seconds)

        #If the current frame has not yet been drawn
        if current_frame > drawn_frame:
            checkerboard_frame = current_frame%2
            image = checkerboard[checkerboard_frame]
            drawn_frame = current_frame

            if current_frame > 0:
                # Push sample after stimulus has been displayed.
                if eeg:
                    timestamp = time()
                    if eeg.backend == "muselsl":
                        marker = [markernames[checkerboard_frame]]
                    else:
                        marker = markernames[checkerboard_frame]
                    eeg.push_sample(marker=marker, timestamp=timestamp)

                if len(event.getKeys()) > 0 or current_interval_seconds > record_duration:
                    stopDrawing = True

                event.clearEvents()

        if use_rift:
            trackingState = mywin.getTrackingState()
            mywin.calcEyePoses(trackingState.headPose.thePose)
            mywin.setDefaultView()
            draw()
        else: 
            draw()

        mywin.flip()

    # Cleanup
    if eeg:
        eeg.stop()

    mywin.close()


def show_instructions(mywin, duration):

    instruction_text = """
    Welcome to the P100 experiment! 
 
    Stay still, focus on the red dot in the centre of the screen, and try not to blink. 

    This block will run for %s seconds.

    Press spacebar to continue. 
    
    """
    instruction_text = instruction_text % duration
    
    mywin.mouseVisible = False

    # Instructions
    text = visual.TextStim(win=mywin, text=instruction_text, color=[-1, -1, -1])
    text.draw()
    mywin.flip()
    event.waitKeys(keyList="space")
