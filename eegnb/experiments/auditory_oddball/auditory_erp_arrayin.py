"""Generate sound-only auditory oddball stimulus presentation.
"""
import time
from optparse import OptionParser
import os
from glob import glob
from random import choice

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event, sound
from eegnb import generate_save_fn


def present(record_duration=120,stim_types=None,itis=None,additional_labels={},secs=0.07,volume=0.8, eeg=None, save_fn=None):

    markernames = [1, 2]
    
    start = time.time()
    
    # Set up trial parameters
    #record_duration = np.float32(duration)
    
    if eeg:
        if save_fn is None:  # If no save_fn passed, generate a new unnamed save file
            save_fn = generate_save_fn(eeg.device_name, 'auditory_erp_arrayin', 'unnamed')
            print(f'No path for a save file was passed to the experiment. Saving data to {save_fn}')
        eeg.start(save_fn, duration=record_duration)

    # Initialize stimuli
    #aud1 = sound.Sound('C', octave=5, sampleRate=44100, secs=secs)
    aud1 = sound.Sound(440,secs=secs)#, octave=5, sampleRate=44100, secs=secs)
    aud1.setVolume(volume)
    
    #aud2 = sound.Sound('D', octave=6, sampleRate=44100, secs=secs)
    aud2 = sound.Sound(528,secs=secs)
    aud2.setVolume(volume)
    auds = [aud1, aud2]
    
    # Setup trial list
    trials = DataFrame(dict(sound_ind=stim_types,iti=itis))
    
    for col_name,col_vec in additional_labels.items():
        trials[col_name] = col_vec
    
    # Setup graphics
    mywin = visual.Window([1920, 1080], monitor='testMonitor', units='deg',
                          fullscr=True)
    fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0, 0], sf=0,
                                  rgb=[1, 0, 0])
    fixation.setAutoDraw(True)
    mywin.flip()
    iteratorthing = 0
    
    
    for ii, trial in trials.iterrows():
        iteratorthing = iteratorthing + 1
        
        # Intertrial interval
        time.sleep(trial['iti'])
        
        # Select and play sound
        ind = int(trial['sound_ind'])
        auds[ind].stop()        
        auds[ind].play()

        additional_stamps = []
        for k in additional_labels.keys():
            additional_stamps += [trial[k]]
        
        # Send marker
        timestamp = time.time()
        
        if eeg: 
            if eeg.backend == 'muselsl':
                #marker = [markernames[label]]
                marker = list(map(int, additional_stamps)) 
                #marker = [additional_stamps]
                
            else:
                #marker = markernames[label]
                marker = additional_stamps
            eeg.push_sample(marker=marker, timestamp=timestamp)   
            
        
        if len(event.getKeys()) > 0 or time.time() - start > record_duration:
            print("breaking")
            print("time.time() - start/duration:")
            print(time.time() - start)
            print(iteratorthing)
            break
        event.clearEvents()
        

    if(time.time() - start < record_duration and iteratorthing == len(stim_types)):
        print("ran out of sounds to play!, time to stall")
        
    while(time.time() - start < record_duration):
        time.sleep(25)
        ind = 1
        auds[ind].stop()        
        auds[ind].play()
    print("done")    
    mywin.close()
        
        
    return trials


def main():
    parser = OptionParser()

    parser.add_option(
        '-d', '--duration', dest='duration', type='int', default=10,
        help='duration of the recording in seconds.')
    parser.add_option(
        '-n', '--n_trials', dest='n_trials', type='int', 
        default=10, help='number of trials.')
    parser.add_option(
        '-i', '--iti', dest='iti', type='float', default=0.3,
        help='intertrial interval')
    parser.add_option(
        '-s', '--soa', dest='soa', type='float', default=0.2,
        help='interval between end of stimulus and next trial.')
    parser.add_option(
        '-j', '--jitter', dest='jitter', type='float', default=0.2,
        help='jitter in the intertrial intervals.')
    parser.add_option(
        '-e', '--secs', dest='secs', type='float', default=0.2,
        help='duration of the sound in seconds.')
    parser.add_option(
        '-v', '--volume', dest='volume', type='float', default=0.8,
        help='volume of the sounds in [0, 1].')
    parser.add_option(
        '-r', '--randomstate', dest='random_state', type='int', 
        default=42, help='random seed')

    (options, args) = parser.parse_args()
    trials_df = present(
        duration=options.duration, n_trials=options.duration, 
        iti=options.iti, soa=options.soa, jitter=options.jitter,
        secs=options.secs, volume=options.volume, 
        random_state=options.random_state) 

    print(trials_df)


if __name__ == '__main__':
    main()
