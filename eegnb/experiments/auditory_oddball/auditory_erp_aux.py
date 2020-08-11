"""Generate sound-only auditory oddball stimulus presentation.
"""
import time
from optparse import OptionParser

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event, sound
from pylsl import StreamInfo, StreamOutlet


def present(duration=120, n_trials=10, iti=0.3, soa=0.2, jitter=0.2, 
            secs=0.2, volume=0.8, random_state=None):
    

    # Create markers stream outlet
    info = StreamInfo('Markers', 'Markers', 1, 0, 'int32', 'myuidw43536')
    outlet = StreamOutlet(info)    

    np.random.seed(random_state)
    markernames = [1, 2]
    start = time.time()

    # Set up trial parameters
    record_duration = np.float32(duration)

    # Initialize stimuli
    aud1 = sound.Sound('C', octave=5, sampleRate=44100, secs=secs)
    aud1.setVolume(volume)
    aud2 = sound.Sound('D', octave=6, sampleRate=44100, secs=secs)
    aud2.setVolume(volume)
    auds = [aud1, aud2]

    # Setup trial list
    sound_ind = np.random.binomial(1, 0.25, n_trials)
    itis = iti + np.random.rand(n_trials) * jitter
    trials = DataFrame(dict(sound_ind=sound_ind, iti=itis))
    trials['soa'] = soa
    trials['secs'] = secs

    for ii, trial in trials.iterrows():
        
        # Intertrial interval
        time.sleep(trial['iti'])

        # Select and play sound
        ind = int(trial['sound_ind'])
        auds[ind].stop()        
        auds[ind].play()

        # Send marker
        timestamp = time.time()
        outlet.push_sample([markernames[ind]], timestamp)
        
        # Offset
        #time.sleep(soa)
        #if (time.time() - start) > record_duration:
        #    break

        # offset
        core.wait(soa)
        if len(event.getKeys()) > 0 or (time.time() - start) > record_duration:
            break
        event.clearEvents()
        
        #if len(event.getKeys()) > 0 or (time() - start) > record_duration:
        #    break
        #event.clearEvents()
        
        
        
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
