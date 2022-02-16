"""Generate sound-only auditory oddball stimulus presentation.
"""
import time
from optparse import OptionParser

import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event, sound
from pylsl import StreamInfo, StreamOutlet

from eegnb import generate_save_fn
from eegnb.devices.eeg import EEG
#from eegnb.stimuli import FACE_HOUSE


def present(duration=120, eeg: EEG=None, save_fn=None,
            stim_types=None, itis=None, additional_labels={},
            secs=0.07, volume=0.8,tone1_hz =440, tone2_hz = 528):

    soa = 0 # ?

    # additional_labels is dict with column names as keys and column vecs as values,
    # that will be added to the dataframe

    # def present(duration=120, n_trials=10, iti=0.3, soa=0.2, jitter=0.2,
    #            secs=0.2, volume=0.8, random_state=None):

    # Create markers stream outlet
    # info = StreamInfo('Markers', 'Markers', 1, 0, 'int32', 'myuidw43536')
    # info = StreamInfo('Markers', 'Markers', 1 + len(additional_labels), 0, 'int32', 'myuidw43536')
    info = StreamInfo(
        "Markers", "Markers", 1 + len(additional_labels), 0, "float32", "myuidw43536"
    )

    outlet = StreamOutlet(info)

    # np.random.seed(random_state)
    markernames = [1, 2]
    start = time.time()

    # Set up trial parameters
    record_duration = np.float32(duration)

    # Initialize stimuli
    # aud1 = sound.Sound('C', octave=5, sampleRate=44100, secs=secs)
    aud1 = sound.Sound(tone1_hz, secs=secs)  # , octave=5, sampleRate=44100, secs=secs)
    aud1.setVolume(volume)

    # aud2 = sound.Sound('D', octave=6, sampleRate=44100, secs=secs)
    aud2 = sound.Sound(tone2_hz, secs=secs)
    aud2.setVolume(volume)
    auds = [aud1, aud2]

    # Setup trial list
    # sound_ind = np.random.binomial(1, 0.25, n_trials)
    # itis = iti + np.random.rand(n_trials) * jitter
    # trials = DataFrame(dict(sound_ind=sound_ind, iti=itis))
    # trials['soa'] = soa
    # trials['secs'] = secs
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

    # Show the instructions screen
    show_instructions(10)

    # Start the EEG stream
    if eeg:
        if save_fn is None:  # If no save_fn passed, generate a new unnamed save file
            # random_id = random.randint(1000,10000)
            random_id = 9999
            save_fn = generate_save_fn(eeg.device_name, "auditory_erp_arrayin", random_id, random_id, "unnamed")
            print(
                f"No path for a save file was passed to the experiment. Saving data to {save_fn}"
            )
        eeg.start(save_fn, duration=record_duration + 5)

    # Start EEG Stream, wait for signal to settle, and then pull timestamp for start point
    start = time.time()

    for ii, trial in trials.iterrows():

        # Intertrial interval
        time.sleep(trial["iti"])

        # Select and play sound
        ind = int(trial["sound_ind"])
        auds[ind].stop()
        auds[ind].play()

        additional_stamps = []
        for k in additional_labels.keys():
            additional_stamps += [trial[k]]

        # Send marker
        #timestamp = time.time()
        # outlet.push_sample([markernames[ind]], timestamp)

        #outlet.push_sample(additional_stamps + [markernames[ind]], timestamp)

        # Offset
        # time.sleep(soa)
        # if (time.time() - start) > record_duration:
        #    break


        # Send marker
        # outlet.push_sample([markernames[ind]], timestamp)
        #outlet.push_sample(additional_stamps + [markernames[ind]], timestamp)

        # Push sample
        if eeg:
            timestamp = time.time()
            if eeg.backend == "muselsl":
                marker = [markernames[ind]]
                #marker = [markernames[label]]
            else:
                marker = markernames[ind]  # type: ignore
            eeg.push_sample(marker=additional_stamps + marker, timestamp=timestamp)

        mywin.flip()

        # offset
        core.wait(soa)
        mywin.flip()
        if len(event.getKeys()) > 0 or (time.time() - start) > record_duration:
            break

        event.clearEvents()

    # Cleanup
    if eeg:
        eeg.stop()

    mywin.close()


    return trials


def show_instructions(duration):

    instruction_text = """
    Welcome to the Auditory Oddball Experiment! 
 
    Stay still, focus on the centre of the screen, listen to the tones, and try not to blink. 

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


def main():
    parser = OptionParser()

    parser.add_option(
        "-d",
        "--duration",
        dest="duration",
        type="int",
        default=10,
        help="duration of the recording in seconds.",
    )
    parser.add_option(
        "-n",
        "--n_trials",
        dest="n_trials",
        type="int",
        default=10,
        help="number of trials.",
    )
    parser.add_option(
        "-i", "--iti", dest="iti", type="float", default=0.3, help="intertrial interval"
    )
    parser.add_option(
        "-s",
        "--soa",
        dest="soa",
        type="float",
        default=0.2,
        help="interval between end of stimulus and next trial.",
    )
    parser.add_option(
        "-j",
        "--jitter",
        dest="jitter",
        type="float",
        default=0.2,
        help="jitter in the intertrial intervals.",
    )
    parser.add_option(
        "-e",
        "--secs",
        dest="secs",
        type="float",
        default=0.2,
        help="duration of the sound in seconds.",
    )
    parser.add_option(
        "-v",
        "--volume",
        dest="volume",
        type="float",
        default=0.8,
        help="volume of the sounds in [0, 1].",
    )
    parser.add_option(
        "-r",
        "--randomstate",
        dest="random_state",
        type="int",
        default=42,
        help="random seed",
    )

    (options, args) = parser.parse_args()
    trials_df = present(
        duration=options.duration,
        n_trials=options.duration,
        iti=options.iti,
        soa=options.soa,
        jitter=options.jitter,
        secs=options.secs,
        volume=options.volume,
        random_state=options.random_state,
    )

    print(trials_df)


if __name__ == "__main__":
    main()
