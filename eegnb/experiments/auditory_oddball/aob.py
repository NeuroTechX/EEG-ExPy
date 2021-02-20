import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event, sound

from time import time

__title__ = "Auditory oddball (orig)"


def present(
    save_fn = None,
    eeg=None,
    duration=120,
    n_trials=2010,
    iti=0.3,
    soa=0.2,
    jitter=0.2,
    secs=0.2,
    volume=0.8,
    random_state=42,
    s1_freq="C",
    s2_freq="D",
    s1_octave=5,
    s2_octave=6,
):

    """

    Auditory Oddball Experiment
    ===========================


    Parameters:
    -----------

    duration - duration of the recording in seconds (default 10)

    n_trials - number of trials (default 10)

    iti - intertrial interval (default 0.3)

    soa - stimulus onset asynchrony, = interval between end of stimulus
          and next trial (default 0.2)

    jitter - jitter in the intertrial intervals (default 0.2)

    secs - duration of the sound in seconds (default 0.2)

    volume - volume of the sounds in [0,1] (default 0.8)

    random_state - random seed (default 42)

    s1_freq - frequency of first tone
    s2_freq - frequency of second tone

    s1_octave - octave of first tone
    s2_octave - octave of second tone

    """

    # Set up trial parameters
    np.random.seed(random_state)
    markernames = [1, 2]
    record_duration = np.float32(duration)

    # Initialize stimuli
    aud1 = sound.Sound(s1_freq, octave=s1_octave, secs=secs)
    aud1.setVolume(volume)
    aud2 = sound.Sound(s2_freq, octave=s2_octave, secs=secs)
    aud2.setVolume(volume)
    auds = [aud1, aud2]

    # Setup trial list
    sound_ind = np.random.binomial(1, 0.25, n_trials)
    itis = iti + np.random.rand(n_trials) * jitter
    trials = DataFrame(dict(sound_ind=sound_ind, iti=itis))
    trials["soa"] = soa
    trials["secs"] = secs

    # Setup graphics
    mywin = visual.Window(
        [1920, 1080], monitor="testMonitor", units="deg", fullscr=True
    )
    fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0, 0], sf=0, rgb=[1, 0, 0])
    fixation.setAutoDraw(True)
    mywin.flip()

    # Show the instructions screen
    show_instructions(10)

    # Start EEG Stream, wait for signal to settle, and then pull timestamp for start point
    if eeg:
        eeg.start(save_fn, duration=record_duration)
    start = time()

    # Iterate through the events
    for ii, trial in trials.iterrows():

        # Intertrial interval
        core.wait(trial["iti"])

        # Select and play sound
        ind = int(trial["sound_ind"])
        auds[ind].stop()
        auds[ind].play()

        # Push sample
        if eeg:
            timestamp = time()
            marker = [markernames[ind]]
            marker = list(map(int, marker))

            eeg.push_sample(marker=marker, timestamp=timestamp)

        mywin.flip()

        # Offset
        core.wait(soa)
        if len(event.getKeys()) > 0:
            break
        if (time() - start) > record_duration:
            break
        event.clearEvents()

    # Cleanup
    if eeg:
        eeg.stop()

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
