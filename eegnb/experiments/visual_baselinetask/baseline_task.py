from time import time
from time import sleep
import os
import random

import numpy as np
from pandas import DataFrame
from psychopy import prefs

prefs.general["audioLib"] = ["pygame"]
from psychopy import visual, core, event, sound
from pylsl import StreamInfo, StreamOutlet, local_clock

# Create markers stream outlet
info = StreamInfo("Markers", "Markers", 1, 0, "int32", "myuidw43536")
outlet = StreamOutlet(info)

start = time()

# Initialize stimuli
aud1 = sound.Sound("C", octave=5, sampleRate=44100, secs=0.5, bits=8)
aud1.setVolume(0.025)

# Setup graphics
mywin = visual.Window([1440, 900], monitor="testMonitor", units="deg", fullscr=True)

# Hide the mouse cursor
mywin.mouseVisible = False

# define the length of each block
exp_length = 20.0

# randomly pick our condition order
cond_order = random.randint(1, 2)

# setup our instructions
instr1 = visual.TextStim(
    mywin,
    text="Keep your eyes open for 20 seconds and focus on the central fixation. You CAN blink during this time. Press the spacebar to begin.",
    pos=(0, -3),
)
instr2 = visual.TextStim(
    mywin,
    text="Keep your eyes closed for 20 seconds, Open them when you hear a long beep/tone. Close them and press the spacebar to begin.",
    pos=(0, -3),
)
instr3 = visual.TextStim(mywin, text="Keep your eyes closed at this time.", pos=(0, -3))
instr4 = visual.TextStim(
    mywin,
    text="You have finished the experiment! Press the spacebar to exit.",
    pos=(0, -3),
)

# setup the fixation
fixation = visual.GratingStim(win=mywin, size=0.1, pos=[0, 0], sf=0, rgb=[1, 1, 1])

core.wait(2)

if cond_order == 1:
    timestamp = local_clock()
    outlet.push_sample([1], timestamp)
    core.wait(1)
    # display instructions for the first eyes-open block
    instr1.setAutoDraw(True)
    fixation.setAutoDraw(True)
    mywin.flip()
    event.waitKeys()

    # start the first eyes-open block
    instr1.setAutoDraw(False)
    mywin.flip()
    timestamp = local_clock()
    outlet.push_sample([11], timestamp)
    core.wait(exp_length)

    # display instructions for the first eyes-closed block
    instr2.setAutoDraw(True)
    mywin.flip()
    event.waitKeys()

    # start first eyes-closed block
    instr2.setAutoDraw(False)
    instr3.setAutoDraw(True)
    mywin.flip()
    timestamp = local_clock()
    outlet.push_sample([21], timestamp)
    aud1.play()
    core.wait(exp_length)
    aud1.play()


elif cond_order == 2:
    timestamp = local_clock()
    outlet.push_sample([2], timestamp)
    core.wait(1)
    # display instructions for the first eyes-closed block
    fixation.setAutoDraw(True)
    instr2.setAutoDraw(True)
    mywin.flip()
    event.waitKeys()

    # start first eyes-closed block
    instr2.setAutoDraw(False)
    instr3.setAutoDraw(True)
    mywin.flip()
    timestamp = local_clock()
    outlet.push_sample([21], timestamp)
    aud1.play()
    core.wait(exp_length)
    aud1.play()

    # display instructions for the first eyes-open block
    instr3.setAutoDraw(False)
    instr1.setAutoDraw(True)
    fixation.setAutoDraw(True)
    mywin.flip()
    event.waitKeys()

    # start the first eyes-open block
    instr1.setAutoDraw(False)
    mywin.flip()
    timestamp = local_clock()
    outlet.push_sample([11], timestamp)
    core.wait(exp_length)


# display end screen
instr3.setAutoDraw(False)
instr4.setAutoDraw(True)
mywin.flip()
event.waitKeys()


# Cleanup
mywin.close()
sleep(5.0)

os.remove("Stop_EEG.csv")
