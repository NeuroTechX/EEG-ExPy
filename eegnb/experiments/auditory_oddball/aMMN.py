import os,sys
from datetime import datetime
from time import time, sleep
from glob import glob
from random import choice
from optparse import OptionParser

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event, sound, prefs, logging
from eegnb import generate_save_fn

import h5py

if sys.platform in ["linux", "linux2"]:
    prefs.resetPrefs()
    prefs.hardware['audioDriver'] = ["portaudio"]
    prefs.hardware['audioLib'] = ['PTB', 'pyo','pygame']


def present(
    save_fn: str = None,
    duration=120,
    stim_types=None,
    itis=None,
    additional_labels={},
    secs=0.07,
    volume=0.8,
    eeg=None,
    fnirs=None
):
    markernames = [1, 2]
    record_duration = np.float32(duration)

    ## Initialize stimuli
    # aud1 = sound.Sound('C', octave=5, sampleRate=44100, secs=secs)
    aud1 = sound.Sound(440, secs=secs)  # , octave=5, sampleRate=44100, secs=secs)
    aud1.setVolume(volume)

    # aud2 = sound.Sound('D', octave=6, sampleRate=44100, secs=secs)
    aud2 = sound.Sound(528, secs=secs)
    aud2.setVolume(volume)
    auds = [aud1, aud2]

    # Setup trial list
    trials = DataFrame(dict(sound_ind=stim_types, iti=itis))

    for col_name, col_vec in additional_labels.items():
        trials[col_name] = col_vec

    # Setup graphics
    mywin = visual.Window(
        [1920, 1080], monitor="testMonitor", units="deg", fullscr=True
    )
    fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0, 0], sf=0, rgb=[1, 0, 0])
    fixation.setAutoDraw(True)
    mywin.flip()
    iteratorthing = 0

    # start the EEG stream, will delay 5 seconds to let signal settle
    if eeg:
        eeg.start(save_fn, duration=record_duration)

    # start the fNIRS device
    if fnirs:
        fnirs.start()#save_fn, duration=record_duration)


    show_instructions(10)

    # Start EEG Stream, wait for signal to settle, and then pull timestamp for start point
    start = time()

    # Iterate through the events
    for ii, trial in trials.iterrows():

        iteratorthing +=1 

        # Inter trial interval
        core.wait(trial["iti"])

        # Select and display image
        ind = int(trial["sound_ind"])
        auds[ind].stop()
        auds[ind].play()


        # Push triggers
        #marker = additional_labels["labels"][iteratorthing - 1]
        
        if trial['sound_ind']==0:
            marker = 1
            marker_name = "deviant"
        elif trial['sound_ind']==1:
            marker = 2
            marker_name = "standard"


        timestamp = time()
        if eeg:
            if eeg.backend == "muselsl":
                #marker = [additional_labels["labels"][iteratorthing - 1]]
                eeg_marker = [marker]
                eeg_marker = list(map(int, eeg_marker))
            else:
                eeg_marker = marker # additional_labels["labels"][iteratorthing - 1]
            eeg.push_sample(marker=eeg_marker, timestamp=timestamp)

        if fnirs:
            marker_name = 'event_' + marker_name
            fnirs.push_sample(timestamp=timestamp, marker=marker,marker_name=marker_name)


        mywin.flip()
        if len(event.getKeys()) > 0:
            break
        if (time() - start) > record_duration:
            break

        event.clearEvents()


        if iteratorthing == 1798:  # Really not sure where this came from
            sleep(10)

    # Cleanup
    if eeg:
        eeg.stop()

    if fnirs: 
        fnirs.stop()

    mywin.close()


def show_instructions(duration):

    instruction_text = """
    Welcome to the aMMN experiment! 
 
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
