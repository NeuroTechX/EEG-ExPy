import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event, logging
from time import time, strftime, gmtime
from optparse import OptionParser
from pylsl import StreamInfo, StreamOutlet
from glob import glob
from random import choice
import random
import math
import os
import scipy.io


def present(subject, session, duration=120):

    outdir = os.getcwd() + "/response_files/"
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    ########################### more muse-lsl code ########################################
    # create
    info = StreamInfo("Markers", "Markers", 1, 0, "int32", "myuidw43536")
    # next make an outlet
    outlet = StreamOutlet(info)
    markernames = [1, 2]

    # Setup log
    # position = np.random.binomial(1, 0.15, n_trials)
    # trials = DataFrame(dict(position=position, timestamp=np.zeros(n_trials)))

    # graphics

    def loadImage(filename):
        return visual.ImageStim(win=mywin, image=filename)

    mywin = visual.Window([900, 500], monitor="testMonitor", units="deg", fullscr=False)
    targets = list(
        map(loadImage, glob("stimulus_presentation/stim/cats_dogs/target-*.jpg"))
    )
    nontargets = list(
        map(loadImage, glob("stimulus_presentation/stim/cats_dogs/nontarget-*.jpg"))
    )

    #######################################################################################

    # code modified from https://github.com/djangraw/PsychoPyParadigms/blob/master/BasicExperiments/GoNoGoTask_d1.py

    # declare primary task params
    params = {
        # Declare stimulus and response parameters
        # time when stimulus is presented (in seconds)
        "stimDur": 0.8,
        # time between when one stimulus disappears and the next appears (in seconds)
        "ISI": 0.5,
        "tStartup": 3,  # pause time before starting first stimulus
        "tCoolDown": 2,  # pause time after end of last stimulus before "the end" text
        "triggerKey": "t",  # key from scanner that says scan is starting
        # keys to be used for responses (mapped to 1,2,3,4)
        "respKeys": ["space"],
        "goStim": "square",  # shape signaling respond
        "noGoStim": "diamond",  # shape signaling don't respond
        "goStimProb": 0.75,  # probability of a given trial being a 'go' trial
        # declare prompt and question files
        "skipPrompts": False,  # go right to the scanner-wait page
        "promptDir": "Prompts/",  # directory containing prompts and questions files
        "promptFile": "GoNoGoPrompts.txt",  # Name of text file containing prompts
        # declare display parameters
        "fullScreen": True,  # run in full screen mode?
        # display on primary screen (0) or secondary (1)?
        "screenToShow": 0,
        "fixCrossSize": 60,  # size of cross, in pixels
        # (x,y) pos of fixation cross displayed before each stimulus (for gaze drift correction)
        "fixCrossPos": [0, 0],
        # in rgb255 space: (r,g,b) all between 0 and 255
        "screenColor": (128, 128, 128),
    }

    n_trials = int(
        (duration - params["tStartup"] - params["tCoolDown"])
        / (params["ISI"] + params["stimDur"])
    )

    screenRes = [800, 600]

    # create clocks and window
    globalClock = core.Clock()  # to keep track of time
    trialClock = core.Clock()  # to keep track of time
    win = visual.Window(
        screenRes,
        fullscr=params["fullScreen"],
        allowGUI=False,
        monitor="testMonitor",
        screen=params["screenToShow"],
        units="deg",
        name="win",
        color=params["screenColor"],
        colorSpace="rgb255",
    )
    # create fixation cross
    fCS = params["fixCrossSize"]  # size (for brevity)
    fCP = params["fixCrossPos"]  # position (for brevity)
    fixation = visual.ShapeStim(
        win,
        lineColor="#000000",
        lineWidth=3.0,
        vertices=(
            (fCP[0] - fCS / 2, fCP[1]),
            (fCP[0] + fCS / 2, fCP[1]),
            (fCP[0], fCP[1]),
            (fCP[0], fCP[1] + fCS / 2),
            (fCP[0], fCP[1] - fCS / 2),
        ),
        units="pix",
        closeShape=False,
        name="fixCross",
    )
    # create text stimuli
    message1 = visual.TextStim(
        win,
        pos=[0, +0.5],
        wrapWidth=1.5,
        color="#000000",
        alignHoriz="center",
        name="topMsg",
        text="aaa",
        units="norm",
    )
    message2 = visual.TextStim(
        win,
        pos=[0, 0],
        wrapWidth=1.5,
        color="#000000",
        alignHoriz="center",
        name="middleMsg",
        text="bbb",
        units="norm",
    )
    message3 = visual.TextStim(
        win,
        pos=[0, -0.5],
        wrapWidth=1.5,
        color="#000000",
        alignHoriz="center",
        name="bottomMsg",
        text="bbb",
        units="norm",
    )

    # draw stimuli
    fCS_rt2 = fCS / math.sqrt(2)
    stims = {"square": [], "diamond": [], "circle": []}
    stims["square"] = visual.ShapeStim(
        win,
        lineColor="#000000",
        lineWidth=3.0,
        vertices=(
            (fCP[0] - fCS / 2, fCP[1] - fCS / 2),
            (fCP[0] + fCS / 2, fCP[1] - fCS / 2),
            (fCP[0] + fCS / 2, fCP[1] + fCS / 2),
            (fCP[0] - fCS / 2, fCP[1] + fCS / 2),
            (fCP[0] - fCS / 2, fCP[1] - fCS / 2),
        ),
        units="pix",
        closeShape=False,
        name="square",
    )
    stims["diamond"] = visual.ShapeStim(
        win,
        lineColor="#000000",
        lineWidth=3.0,
        vertices=(
            (fCP[0], fCP[1] - fCS_rt2),
            (fCP[0] - fCS_rt2, fCP[1]),
            (fCP[0], fCP[1] + fCS_rt2),
            (fCP[0] + fCS_rt2, fCP[1]),
            (fCP[0], fCP[1] - fCS_rt2),
        ),
        units="pix",
        closeShape=False,
        name="diamond",
    )
    stims["circle"] = visual.Circle(
        win, lineColor="#000000", lineWidth=3.0, radius=fCS_rt2, edges=32, units="pix"
    )

    tNextFlip = [0.0]

    def AddToFlipTime(tIncrement=1.0):
        tNextFlip[0] += tIncrement

    # record responses, accuracy, etc. (added by AE)
    responses = []
    hits_go = 0
    hits_nogo = 0
    fa_go = 0
    fa_nogo = 0
    count_go = 0
    count_nogo = 0
    rt = np.zeros((n_trials, 1))

    for iTrial in range(0, n_trials):

        # Decide Trial Params
        isGoTrial = random.random() < params["goStimProb"]

        # display info to experimenter
        print(
            (
                "Running Trial %d: isGo = %d, ISI = %.1f"
                % (iTrial, isGoTrial, params["ISI"])
            )
        )

        if iTrial == 0:
            AddToFlipTime(2)
        fixation.draw()
        while globalClock.getTime() < tNextFlip[0]:
            pass
        win.flip()
        tStimStart = globalClock.getTime()  # record time when window flipped
        # set up next win flip time after this one
        AddToFlipTime(params["ISI"])  # add to tNextFlip[0]

        # Draw stim
        if isGoTrial:
            stims[params["goStim"]].draw()
            win.logOnFlip(
                level=logging.EXP, msg="Display go stim (%s)" % params["goStim"]
            )
            timestamp = time()
            outlet.push_sample([markernames[0]], timestamp)
        else:
            stims[params["noGoStim"]].draw()
            win.logOnFlip(
                level=logging.EXP, msg="Display no-go stim (%s)" % params["noGoStim"]
            )
            timestamp = time()
            outlet.push_sample([markernames[1]], timestamp)
        # Wait until it's time to display
        while globalClock.getTime() < tNextFlip[0]:
            pass
        # log & flip window to display image
        win.flip()
        tStimStart = globalClock.getTime()  # record time when window flipped
        # set up next win flip time after this one
        AddToFlipTime(params["stimDur"])  # add to tNextFlip[0]

        # Flush the key buffer and mouse movements
        event.clearEvents()
        # Wait for relevant key press or 'stimDur' seconds
        respKey = None
        thisKey = None
        t = None
        # until it's time for the next frame
        while globalClock.getTime() < tNextFlip[0]:
            # get new keys
            # newKeys = event.getKeys(keyList=params['respKeys']+['q','escape'],timeStamped=globalClock)
            newKeys = event.getKeys(timeStamped=globalClock)
            # check each keypress for escape or response keys
            if len(newKeys) > 0:
                for thisKey in newKeys:
                    respKey = thisKey[0]
                    t = globalClock.getTime() - tStimStart
                    # tempArray = [iTrial, isGoTrial, respKey[0]]
                    # responses.append(tempArray)
                    if thisKey[0] in ["q", "escape"]:  # escape keys
                        CoolDown()  # exit gracefully
                    # only take first keypress
                    elif thisKey[0] in params["respKeys"] and respKey == None:
                        respKey = thisKey  # record keypress

        tempArray = [iTrial, isGoTrial, respKey, t]
        responses.append(tempArray)
        if isGoTrial:
            count_go += 1
        else:
            count_nogo += 1

        if isGoTrial:
            if respKey == "space":
                hits_go += 1
            else:
                fa_go += 1
        elif ~isGoTrial:
            if respKey == None:
                hits_nogo += 1
            else:
                fa_nogo += 1

        # get RT for correct go trials
        if isGoTrial and respKey == "space":
            rt[iTrial] = t
        else:
            rt[iTrial] = np.nan

        # Display the fixation cross
        if params["ISI"] > 0:  # if there should be a fixation cross
            fixation.draw()  # draw it
            win.logOnFlip(level=logging.EXP, msg="Display Fixation")
            win.flip()

        # return
        if iTrial == n_trials:
            AddToFlipTime(params["tCoolDown"])

    fixation.draw()
    win.flip()
    while globalClock.getTime() < tNextFlip[0]:
        pass

    acc_go = np.round(float(hits_go) / float(count_go) * float(100), 2)
    acc_nogo = np.round(float(hits_nogo) / float(count_nogo) * float(100), 2)
    mean_rt = np.round(float(np.nanmean(rt)), 2)

    outname = outdir + "behav_" + subject + "_run" + str(session) + ".mat"
    scipy.io.savemat(
        outname,
        {
            "rt": rt,
            "mean_rt": mean_rt,
            "acc_go": acc_go,
            "acc_nogo": acc_nogo,
            "hits_go": hits_go,
            "hits_nogo": hits_nogo,
            "fa_go": fa_go,
            "fa_nogo": fa_nogo,
            "count_go": count_go,
            "count_nogo": count_nogo,
        },
    )

    # display results
    message1.setText("That's the end! Here are your results:")
    message2.setText(
        "N trials = %d \nGo accuracy = %d/%d (%0.2f) \nNoGo accuracy = %d/%d (%0.2f) \nMean correct Go RT = %0.2f"
        % (
            params["nTrials"],
            hits_go,
            count_go,
            round(acc_go, 2),
            hits_nogo,
            count_nogo,
            round(acc_nogo, 2),
            round(mean_rt, 2),
        )
    )
    message3.setText("Press 'q' or 'escape' to end the session.")
    win.logOnFlip(level=logging.EXP, msg="Display TheEnd")
    message1.draw()
    message2.draw()
    message3.draw()
    win.flip()
    thisKey = event.waitKeys(keyList=["q", "escape"])
    core.quit()
    mywin.close()


def main():
    parser = OptionParser()
    parser.add_option(
        "-s", "--subject", dest="subject", type="string", help="name of subject."
    )
    parser.add_option(
        "-n", "--session", dest="session", type="int", help="number of session."
    )
    parser.add_option(
        "-d",
        "--duration",
        dest="duration",
        type="int",
        default=120,
        help="duration of the recording in seconds.",
    )

    (options, args) = parser.parse_args()
    present(options.subject, options.session, options.duration)


if __name__ == "__main__":
    main()
