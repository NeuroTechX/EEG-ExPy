"""
Generate Steady-State Auditory Evoked Potential (SSAEP)
=======================================================

Steady-State Auditory Evoked Potential (SSAEP) - also known as Auditory
Steady-State Response (ASSR) - stimulus presentation.

"""

from optparse import OptionParser

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event, sound
from pylsl import StreamInfo, StreamOutlet

import os
from time import time, sleep
from glob import glob
from random import choice
from optparse import OptionParser

from eegnb import generate_save_fn

from scipy import stats

def present(duration=120, n_trials=2010, iti=0.5, soa=3.0, jitter=0.2, 
            volume=0.8, random_state=42, eeg=None, save_fn=None,
            cf1=900, amf1=45, cf2=770, amf2=40.018,sample_rate=44100):

    """

    Auditory SSAEP Experiment
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


    """


    # Set up trial parameters
    np.random.seed(random_state)
    markernames = [1, 2]
    record_duration = np.float32(duration)


    # Initialize stimuli
    am1 = generate_am_waveform(cf1, amf1, secs=soa, sample_rate=sample_rate)
    am2 = generate_am_waveform(cf2, amf2, secs=soa, sample_rate=sample_rate)

    aud1 = sound.Sound(am1,sampleRate=sample_rate)
    aud1.setVolume(volume)
    aud2 = sound.Sound(am2,sampleRate=sample_rate)
    aud2.setVolume(volume)
    auds = [aud1, aud2]


    # Set up trial list
    stim_freq = np.random.binomial(1, 0.5, n_trials)
    itis = iti + np.random.rand(n_trials) * jitter
    trials = DataFrame(dict(stim_freq=stim_freq, timestamp=np.zeros(n_trials)))
    trials['iti'] = itis
    trials['soa'] = soa


    # Setup graphics
    mywin = visual.Window([1920, 1080], monitor='testMonitor', units='deg',
                          fullscr=True)
    fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0, 0], sf=0,
                                  rgb=[1, 0, 0])
    fixation.setAutoDraw(True)
    mywin.flip()
    

    # Show the instructions screen
    show_instructions(10)


    # Start EEG Stream, wait for signal to settle, and then pull timestamp for start point
    if eeg:
        if save_fn is None:  # If no save_fn passed, generate a new unnamed save file
            save_fn = generate_save_fn(eeg.device_name, 'auditoryaMMN', 'unnamed')
            print(f'No path for a save file was passed to the experiment. Saving data to {save_fn}')
        eeg.start(save_fn,duration=record_duration)
    start = time()


    # Iterate through the events
    for ii, trial in trials.iterrows():
        
        # Intertrial interval
        core.wait(trial['iti'] + np.random.randn() * jitter )
        
        # Select stimulus frequency
        ind = trials['stim_freq'].iloc[ii]

        auds[ind].stop()
        auds[ind].play()

        # Push sample
        if eeg:
            timestamp = time()
            if eeg.backend == 'muselsl':
                marker = [markernames[ind]]
                marker = list(map(int, marker))
            else:
                marker = markernames[ind]
                
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
    if eeg: eeg.stop()

    mywin.close()




def show_instructions(duration):

    instruction_text = \
    """
    Welcome to the aMMN experiment!

    Stay still, focus on the centre of the screen, and try not to blink.

    This block will run for %s seconds.

    Press spacebar to continue.

    """
    instruction_text = instruction_text %duration

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



def generate_am_waveform(carrier_freq, am_freq, secs=1, sample_rate=None,
                             am_type='gaussian', gaussian_std_ratio=8):
        """Generate an amplitude-modulated waveform.

        Generate a sine wave amplitude-modulated by a second sine wave or a
        Gaussian envelope with standard deviation = period_AM/8.

        Args:
            carrier_freq (float): carrier wave frequency, in Hz
            am_freq (float): amplitude modulation frequency, in Hz

        Keyword Args:
            secs (float): duration of the stimulus, in seconds
            sample_rate (float): sampling rate of the sound, in Hz
            am_type (str): amplitude-modulation type
                'gaussian' -> Gaussian with std defined by `gaussian_std`
                'sine' -> sine wave
            gaussian_std_ratio (float): only used if `am_type` is 'gaussian'.
                Ratio between AM period and std of the Gaussian envelope. E.g.,
                gaussian_std = 8 means the Gaussian window has 8 standard
                deviations around its mean inside one AM period.

        Returns:
            (numpy.ndarray): sound samples
        """
        t = np.arange(0, secs, 1./sample_rate)

        if am_type == 'gaussian':
            period = int(sample_rate / am_freq)
            std = period / gaussian_std_ratio
            norm_window = stats.norm.pdf(np.arange(period), period / 2, std)
            norm_window /= np.max(norm_window)
            n_windows = int(np.ceil(secs * am_freq))
            am = np.tile(norm_window, n_windows)
            am = am[:len(t)]

        elif am_type == 'sine':
            am = np.sin(2 * np.pi * am_freq * t)

        carrier = 0.5 * np.sin(2 * np.pi * carrier_freq * t) + 0.5
        am_out = carrier * am

        return am_out


