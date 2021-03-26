import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event
from time import time, strftime, gmtime
from optparse import OptionParser
from pylsl import StreamInfo, StreamOutlet
import scipy.io
import os
import sys


def present(duration, subject, session):
    # create
    info = StreamInfo("Markers", "Markers", 1, 0, "int32", "myuidw43536")

    # next make an outlet
    outlet = StreamOutlet(info)

    # 11-InvalidLeft; 12-InvalidRight; 21-ValidLeft; 22-ValidRight
    markernames = [11, 12, 21, 22]
    # 1 - Cue Left, 2 - Cue Right
    cue_markernames = [1, 2]
    # 31 - incorrect, 32 - Correct
    resp_markernames = [31, 32]

    n_trials = 2010
    instruct = 1
    practicing = 1

    # seconds
    iti = 1
    iti_jitter = 0.2
    cue_target = 1.5
    cue_target_jitter = 0.5
    target_length = 0.05

    cue_validity = 0.80
    record_duration = np.float32(duration)

    target_positions = [-10, 10]
    target_size = [1]

    # Setup log
    tilt = np.random.binomial(1, 0.5, n_trials)
    cues = np.random.binomial(1, 0.5, n_trials)

    trials = DataFrame(dict(tilt=tilt, cues=cues))

    # Instructions function below
    if instruct:
        instructions()
    if practicing:
        practice()

    # graphics
    mywin = visual.Window([1440, 900], monitor="testMonitor", units="deg", fullscr=True)

    mywin.mouseVisible = False

    grating = visual.GratingStim(win=mywin, mask="gauss", size=target_size, sf=5)
    fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0, 0], sf=0)
    cuewin = visual.GratingStim(win=mywin, mask="circle", size=0.5, pos=[0, 1], sf=0)

    # saving trial information for output
    responses = []

    # Get ready screen
    text = visual.TextStim(
        win=mywin,
        text="Find the arrow keys, and begin fixating now. The first trial is about to begin",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    text.draw()
    fixation.draw()
    mywin.flip()
    core.wait(3)

    # create a clock for rt's
    clock = core.Clock()
    # create a timer for the experiment and EEG markers
    start = time()

    for ii, trial in trials.iterrows():

        til = trials["tilt"].iloc[ii]
        cue = trials["cues"].iloc[ii]
        # cue direction, pick target side
        if cue:
            cuewin.color = [1, 0, 0]
            pos = int(np.random.binomial(1, cue_validity, 1))
        else:
            cuewin.color = [0, 0, 1]
            pos = int(np.random.binomial(1, 1 - cue_validity, 1))
        # create target
        if pos:
            grating.pos = [10, 0]
        else:
            grating.pos = [-10, 0]

        # 1- Valid cue, 0 - Invalid
        validity = int(not abs(cue - pos))

        # til, 1 - Horizontal, 0 - Vertical
        grating.ori = 90 * til
        grating.phase += np.random.rand()

        ## Trial starts here ##
        # inter trial interval
        core.wait(iti + np.random.rand() * iti_jitter)

        # cueonset
        cuewin.draw()
        fixation.draw()
        t_cueOnset = time()
        # 1 - Cue Left, 2 - Cue Right
        outlet.push_sample([cue_markernames[cue]], t_cueOnset)
        mywin.flip()

        # targonset
        core.wait(cue_target + np.random.rand() * cue_target_jitter)
        grating.draw()
        fixation.draw()
        cuewin.draw()
        t_targetOnset = time()

        # 11-InvalidLeft; 12-InvalidRight; 21-ValidLeft; 22-ValidRight
        outlet.push_sample([markernames[pos + (validity * 2)]], t_targetOnset)
        mywin.flip()

        # response period
        core.wait(target_length)
        fixation.draw()
        t_respOnset = clock.getTime()
        mywin.flip()

        # Wait for response
        keys = event.waitKeys(keyList=["right", "up"], timeStamped=clock)
        # categorize response
        correct = 1
        response = 1
        # if validity:
        # print("Valid Target")
        # else:
        # print("Invalid Target")

        if keys[0][0] == "right":
            # print("pressed horizontal")
            response = 1
            if til:
                # print("Correct")
                correct = 1
            else:
                # print("Incorrect")
                # play sound
                sys.stdout.write("\a")
                correct = 0
        elif keys[0][0] == "up":
            # print("pressed vertical")
            response = 0
            if til:
                # print("Incorrect")
                sys.stdout.write("\a")
                correct = 0
            else:
                # print("Correct")
                correct = 1

        # reset sound
        sys.stdout.flush()

        # meausure RT
        rt = keys[0][1] - t_respOnset
        # print("RT = " + str(np.round(rt*1000)) + " ms")

        # save variables
        tempArray = [ii + 1, cue, pos, validity, til, response, correct, rt * 1000]
        # print(tempArray)
        responses.append(tempArray)
        column_labels = [
            "trial",
            "cue direction",
            "target position",
            "cue validity",
            "target tilt",
            "response",
            "accuracy",
            "rt",
        ]
        # trial number (start at 1)
        # Pos, cue - 1 right
        # validity - 1 valid
        # til = 1 - horizontal; 0 - vertical
        # response - 1 right arrow (horizontal); 0 up arrow (vertical)
        # correct - 1 correct, 0 incorrect
        # rt - ms

        # block end
        if (time() - start) > record_duration:
            break
        event.clearEvents()

    # save the behavioural data into matlab file
    directory = os.path.join(
        os.path.expanduser("~"),
        "eeg-notebooks",
        "data",
        "visual",
        "cueing",
        "subject" + str(subject),
        "session" + str(session),
    )
    if not os.path.exists(directory):
        os.makedirs(directory)
    outname = os.path.join(
        directory,
        "subject"
        + str(subject)
        + "_session"
        + str(session)
        + ("_behOutput_%s.mat" % strftime("%Y-%m-%d-%H.%M.%S", gmtime())),
    )
    output = np.array(responses)
    scipy.io.savemat(outname, {"output": output, "column_labels": column_labels})

    # Overall Accuracy
    print("Overall Mean Accuracy = " + str(round(100 * np.mean(output[:, 6]))))
    # Overall Mean, Median RT
    print("Overall Mean RT = " + str(round(np.mean(output[:, 7]))))
    print("Overall Median RT = " + str(round(np.median(output[:, 7]))))

    ## Mean RT
    print("Valid Mean RT = " + str(round(np.mean(output[output[:, 3] == 1, 7]))))
    print("Invalid Mean RT = " + str(round(np.mean(output[output[:, 3] == 0, 7]))))
    print("Valid Median RT = " + str(round(np.median(output[output[:, 3] == 1, 7]))))
    print("Invalid Median RT = " + str(round(np.median(output[output[:, 3] == 0, 7]))))

    # Goodbye Screen
    text = visual.TextStim(
        win=mywin,
        text="Thank you for participating. Press spacebar to exit the experiment.",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    text.draw()
    mywin.flip()
    event.waitKeys(keyList="space")

    mywin.mouseVisible = True

    # Cleanup
    mywin.close()


def practice():

    practice_duration = 20
    n_trials = 2010

    # seconds
    iti = 1
    iti_jitter = 0.2
    cue_target = 1.5
    cue_target_jitter = 0.5
    target_length = 0.2

    cue_validity = 0.99

    record_duration = np.float32(practice_duration)

    target_positions = [-10, 10]
    target_size = [2]

    # Setup log
    tilt = np.random.binomial(1, 0.5, n_trials)
    cues = np.random.binomial(1, 0.5, n_trials)

    trials = DataFrame(dict(tilt=tilt, cues=cues))

    # graphics
    mywin = visual.Window([1440, 900], monitor="testMonitor", units="deg", fullscr=True)
    grating = visual.GratingStim(win=mywin, mask="gauss", size=2, sf=4)
    fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0, 0], sf=0)
    cuewin = visual.GratingStim(win=mywin, mask="circle", size=0.5, pos=[0, 1], sf=0)

    mywin.mouseVisible = False

    # Get ready screen
    text = visual.TextStim(
        win=mywin,
        text="Find the arrow keys, and begin fixating now. The first practice trial is about to begin",
        color=[-1, -1, -1],
        pos=[0, 5],
    )

    text.draw()
    fixation.draw()
    mywin.flip()
    core.wait(5)

    # create a clock for rt's
    clock = core.Clock()
    # create a timer for the experiment and EEG markers
    start = time()

    for ii, trial in trials.iterrows():

        til = trials["tilt"].iloc[ii]
        cue = trials["cues"].iloc[ii]
        # cue direction, pick target side
        if cue:
            cuewin.color = [1, 0, 0]
            pos = int(np.random.binomial(1, cue_validity, 1))
        else:
            cuewin.color = [0, 0, 1]
            pos = int(np.random.binomial(1, 1 - cue_validity, 1))
        # create target
        if pos:
            grating.pos = [10, 0]
        else:
            grating.pos = [-10, 0]

        # 1- Valid cue, 0 - Invalid
        validity = int(not abs(cue - pos))

        # til, 1 - Horizontal, 0 - Vertical
        grating.ori = 90 * til
        grating.phase += np.random.rand()

        ## Trial starts here ##
        # inter trial interval
        core.wait(iti + np.random.rand() * iti_jitter)

        # cueonset
        cuewin.draw()
        fixation.draw()
        # 1 - Cue Left, 2 - Cue Right
        mywin.flip()

        # targonset
        core.wait(cue_target + np.random.rand() * cue_target_jitter)
        grating.draw()
        fixation.draw()
        cuewin.draw()

        # 11-InvalidLeft; 12-InvalidRight; 21-ValidLeft; 22-ValidRight
        mywin.flip()

        # response period
        core.wait(target_length)
        fixation.draw()
        mywin.flip()

        # Wait for response
        keys = event.waitKeys(keyList=["right", "up"], timeStamped=clock)
        # categorize response
        correct = 1
        response = 1
        # if validity:
        # print("Valid Target")
        # else:
        # print("Invalid Target")

        if keys[0][0] == "right":
            # print("pressed horizontal")
            response = 1
            if til:
                # print("Correct")
                correct = 1
            else:
                # print("Incorrect")
                # play sound
                sys.stdout.write("\a")
                correct = 0
        elif keys[0][0] == "up":
            # print("pressed vertical")
            response = 0
            if til:
                # print("Incorrect")
                sys.stdout.write("\a")
                correct = 0
            else:
                # print("Correct")
                correct = 1

        # reset sound
        sys.stdout.flush()

        # block end
        if (time() - start) > record_duration:
            break
        event.clearEvents()

    # End Practice Screen
    text = visual.TextStim(
        win=mywin,
        text="That is the end of the practice, Please let the experimenter know if you have any questions. Press Spacebar to begin the first trial.",
        color=[-1, -1, -1],
        pos=[0, 5],
    )

    text.draw()
    fixation.draw()
    mywin.flip()
    event.waitKeys(keyList="space")

    mywin.mouseVisible = True

    # Cleanup
    mywin.close()


def instructions():

    # graphics
    mywin = visual.Window([1440, 900], monitor="testMonitor", units="deg", fullscr=True)
    grating = visual.GratingStim(win=mywin, mask="gauss", size=2, sf=4)
    fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0, 0], sf=0)
    cuewin = visual.GratingStim(win=mywin, mask="circle", size=0.5, pos=[0, 1], sf=0)

    mywin.mouseVisible = False

    # Instructions
    text = visual.TextStim(
        win=mywin,
        text="Welcome to the Attention Experiment!, Press spacebar to continue",
        color=[-1, -1, -1],
    )
    text.draw()
    mywin.flip()
    event.waitKeys(keyList="space")

    # Instructions
    text = visual.TextStim(
        win=mywin,
        text="These are these are the stimuli you will see on each trial.",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    grating.pos = [10, 0]
    cuewin.color = [1, 0, 0]
    grating.draw()
    cuewin.draw()
    fixation.draw()
    text.draw()
    mywin.flip()
    event.waitKeys(keyList="space")

    # Instructions
    text = visual.TextStim(
        win=mywin,
        text="Each trial will begin with the white fixation point, keep your eyes focused on this position the entire trial. Try not to blink. Keep still. ",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    text.draw()
    fixation.draw()
    mywin.flip()
    event.waitKeys(keyList="space")

    # Instructions
    text = visual.TextStim(
        win=mywin,
        text="After a moment, a coloured circle will appear above the fixation. This is your attention cue. If it is RED, the target will more likely appear on the RIGHT",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    cuewin.color = [1, 0, 0]
    cuewin.draw()
    text.draw()
    fixation.draw()
    mywin.flip()
    event.waitKeys(keyList="space")

    # Instructions
    text = visual.TextStim(
        win=mywin,
        text="If it is BLUE, the target will more likely appear on the LEFT, sometimes the target can still appear at the unattended side.",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    cuewin.color = [0, 0, 1]
    cuewin.draw()
    text.draw()
    fixation.draw()
    mywin.flip()
    event.waitKeys(keyList="space")

    # Instructions
    text = visual.TextStim(
        win=mywin,
        text="After another delay, the target will briefly appear, most often in the side cued by the coloured circle. The target can either be tilted vertically like this...",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    til = 0
    grating.ori = 90 * til
    grating.pos = [10, 0]
    cuewin.color = [1, 0, 0]
    grating.draw()
    cuewin.draw()
    text.draw()
    fixation.draw()
    mywin.flip()
    event.waitKeys(keyList="space")

    # Instructions
    text = visual.TextStim(
        win=mywin,
        text="Or Horizontally like this. Your task is to press the RIGHT ARROW if the target is horizontal ",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    til = 1
    grating.ori = 90 * til
    grating.pos = [-10, 0]
    cuewin.color = [0, 0, 1]
    grating.draw()
    cuewin.draw()
    text.draw()
    fixation.draw()
    mywin.flip()
    event.waitKeys(keyList="space")

    # Instructions
    text = visual.TextStim(
        win=mywin,
        text="Or the UP ARROW if it is vertical. You should respond as fast and accurately as you can. Respond no matter which side the target appears, cued or uncued, left or right. ",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    til = 0
    grating.ori = 90 * til
    grating.pos = [-10, 0]
    cuewin.color = [0, 0, 1]
    grating.draw()
    cuewin.draw()
    text.draw()
    fixation.draw()
    mywin.flip()
    event.waitKeys(keyList="space")

    # Instructions
    text = visual.TextStim(
        win=mywin,
        text="After you respond, you will hear a beep if you indicated the wrong direction, and the next trial begins with the fixation cross. You will complete a block of trials. Press Spacebar to begin the practice.",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    fixation.draw()
    text.draw()
    mywin.flip()
    # play sound
    sys.stdout.write("\a")
    sys.stdout.flush()

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
        default=120,
        help="duration of the recording in seconds.",
    )
    parser.add_option(
        "-s",
        "--subject",
        dest="subject",
        type="int",
        default=1,
        help="subject number: must be an integer",
    )
    parser.add_option(
        "-r",
        "--run",
        dest="run",
        type="int",
        default=1,
        help="run (session) number: must be an integer",
    )

    (options, args) = parser.parse_args()
    present(options.duration, options.subject, options.n)


if __name__ == "__main__":
    main()
