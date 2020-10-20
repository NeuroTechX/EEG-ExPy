import os
from time import time
from glob import glob
from random import choice
from optparse import OptionParser

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event, sound

from eegnb import generate_save_fn
#from eegnb.stimuli import FACE_HOUSE


def present(duration=120, eyes='open', chunk_len = 30, eeg=None, save_fn=None,beep_secs=0.07,beep_vol=0.8):

    """
    Resting state experiment with a 'beep'

    This experiment runs a simple resting state recording. 
    
    Visual instructions are presented at the start. 
    
    Markers are laid down at regular intervals, as specified by the 'chunk_len' input parameter. 
    The resultant segments are referred to as 'pseudo-trials', because they appear completely continuous to the user. 
    The reason for using pseudo-trials is  to facilitate resting-state analyses that involve breaking the recording 
    down into segments. The default is to use 30s chunks, and we recommend to stick with this. 

    There are two possible conditions: eyes open and eyes closed. 
    The condition being run is defined by the value of the 'eyes' input parameter

    This in turn leads to one of two behaviours:

    a) Instructions for 'eyes open' are shown, and all pseudo-trials are given the integer marker '1'

    b) Instructions for 'eyes closed' are shown, and all pseudo-trials are given the integer marker '2'

    A beep indicates the start and end of the experiment. 
    (this is particularly intended for the eyes-closed condition)

    
    """
    
    n_trials = 2010 # this is a dummy number; n trials is actually set by duration
    iti = 0.4
    soa = chunk_len #soa = 30 #0.3   i.e., trial duration 30s
    jitter = 0.2
    record_duration = np.float32(duration)

    # Define marker values
    if eyes=='open':
        eyesmarker = 1
    elif eyes=='closed':
        eyesmarker = 2
   

    # Initialize stimuli
    aud1 = sound.Sound(440,secs=beep_secs)#, octave=5, sampleRate=44100, secs=secs)
    aud1.setVolume(beep_vol)



    # Start the EEG stream, will delay 5 seconds to let signal settle

    # Setup graphics
    mywin = visual.Window([1600, 900], monitor='testMonitor', units="deg", fullscr=True)

    # Show the instructions screen
    show_instructions(duration,eyes)

    if eeg:
        if save_fn is None:  # If no save_fn passed, generate a new unnamed save file
            save_fn = generate_save_fn(eeg.device_name, 'rest_beep', 'unnamed') # visual_n170', 'unnamed')
            print(f'No path for a save file was passed to the experiment. Saving data to {save_fn}')
        eeg.start(save_fn, duration=record_duration+5)

    # Start EEG Stream, wait for signal to settle, and then pull timestamp for start point
    start = time()

    # Play the beep indicating the start of the rest period
    aud1.stop()
    aud1.play()


 
    # Iterate through the (pseudo-)trials 
    for ii in range(n_trials):
        
        # Inter trial interval
        core.wait(iti + np.random.rand() * jitter)
    
        # Push sample

        if eeg: 
            timestamp = time()
            if eeg.backend == 'muselsl':
                marker = [eyesmarker]
            else:
                marker = eyesmarker
            eeg.push_sample(marker=marker, timestamp=timestamp)
     
        #mywin.flip()
    
        # offset
        core.wait(soa)
        #mywin.flip()
        if len(event.getKeys()) > 0 or (time() - start) > record_duration:
            break
    
        event.clearEvents()


    # Play the beep indicating the end of the rest period
    aud1.stop()
    aud1.play()


    # Cleanup
    if eeg: eeg.stop()

    mywin.close()




def show_instructions(duration,eyes):


    if eyes=='open':
        eyes_line = 'This is the "eyes open" condition. When the block starts, keep your eyes open and fixed on the centre of the screen.'
    elif eyes=='closed':
        eyes_line = 'This is the "eyes closed" condition. When the block starts, Keep your eyes closed, but don''t fall asleep!'
        

    instruction_text = \
    """
    Welcome to the Resting state experiment! 
    
    Stay still, relax. 
    This block will run for %s seconds. 

    %s 
    You will hear a tone at the start and the end of the block. After the second tone, you can relax. 

    Press spacebar to continue. 
    
    """
    instruction_text = instruction_text %(duration,eyes_line)

    # graphics
    mywin = visual.Window([1600, 900], monitor="testMonitor", units="deg",
                          fullscr=True)

    mywin.mouseVisible = False

    #Instructions
    text = visual.TextStim(
        win=mywin,
        text=instruction_text,
        color=[-1, -1, -1])
    text.draw()
    mywin.flip()
    event.waitKeys(keyList="space")

    mywin.mouseVisible = True
    mywin.close()
