"""
Generate N170
=============

Face vs. house paradigm stimulus presentation for evoking present.

"""

from time import time
from optparse import OptionParser
import os
from glob import glob
from random import choice

import numpy as np
from pandas import DataFrame,read_csv
from psychopy import visual, core, event
from pylsl import StreamInfo, StreamOutlet

from eegnb import stimuli,experiments
stim_dir = os.path.split(stimuli.__file__)[0]
exp_dir = os.path.split(experiments.__file__)[0]

# fixed stim order list file
fso_list_file = os.path.join(exp_dir, 'visual_n170', 'n170_fixedstimorder_list.csv')


def present(duration=120):

    # Create markers stream outlet
    #info = StreamInfo('Markers', 'Markers', 1, 0, 'int32', 'myuidw43536')
    info = StreamInfo('Markers', 'Markers', 3, 0, 'int32', 'myuidw43536')
    outlet = StreamOutlet(info)

    #markernames = [1, 2]
    start = time()

    # Set up trial parameters
    #n_trials = 2010
    iti = 0.8
    soa = 0.2
    jitter = 0.2
    record_duration = np.float32(duration)

    # Setup trial list
    #image_type = np.random.binomial(1, 0.5, n_trials)
    #trials = DataFrame(dict(image_type=image_type,
    #                        timestamp=np.zeros(n_trials)))

    
    fso_ims = read_csv(fso_list_file)
    n_trials = fso_ims.shape[0]
    
    
    # Setup graphics

    def load_image(filename):
        return visual.ImageStim(win=mywin, image=filename)

    mywin = visual.Window([1600, 900], monitor='testMonitor', units='deg', winType='pygame',
                          fullscr=True)
    
    #faces = list(map(load_image, glob(
    #    'stimulus_presentation/stim/face_house/faces/*_3.jpg')))
    #houses = list(map(load_image, glob(
    #    'stimulus_presentation/stim/face_house/houses/*.3.jpg')))
    

    #for ii, trial in trials.iterrows():
    for ii,trial in fso_ims.iterrows():

        trialnum,filename,facehouse,girlboy = trial.values
        filename = os.path.join(stim_dir, filename)        

        # Intertrial interval
        core.wait(iti + np.random.rand() * jitter)
    
        # Select and display image
        #label = trials['image_type'].iloc[ii]
        #image = choice(faces if label == 1 else houses)
        image = load_image(filename)
        
        image.draw()
     
        # Send marker
        timestamp = time()
        #outlet.push_sample([markernames[label]], timestamp)
        outlet.push_sample([trialnum,facehouse+1,girlboy+1], timestamp)
        
        mywin.flip()
    
        # offset
        core.wait(soa)
        mywin.flip()
        if len(event.getKeys()) > 0 or (time() - start) > record_duration:
            break
        event.clearEvents()

    # Cleanup
    mywin.close()


def main():
    parser = OptionParser()

    parser.add_option("-d", "--duration",
                      dest="duration", type='int', default=120,
                      help="duration of the recording in seconds.")

    (options, args) = parser.parse_args()
    present(options.duration)


if __name__ == '__main__':
    main()
