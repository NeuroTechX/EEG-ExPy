from time import time, strftime, gmtime
from typing import List

import numpy as np
import pandas as pd
from psychopy import visual, core, event

from eegnb import get_recording_dir


# TODO: These default values are bad, they should be passed down correctly
def present(duration: int, eeg, subject=0, session=0, **kwargs) -> None:
    # 1 - Code
    # 2 - Prose
    cue_markernames = [1, 2]

    n_trials = 20
    instruct = 1
    practicing = 1

    # seconds
    cue_target = 1.5
    cue_target_jitter = 0.5
    target_length = 0.05

    cue_validity = 0.80
    record_duration = np.float32(duration)

    # Setup log
    codeorprose = np.random.binomial(1, 0.5, n_trials)

    trials = pd.DataFrame(dict(codeorprose=codeorprose))

    # Instructions function below
    # TODO: Implement instructions and practice
    if instruct:
        # instructions()
        pass
    if practicing:
        # practice()
        pass

    # graphics
    mywin = visual.Window([1440, 900], monitor="testMonitor", units="deg", fullscr=True)
    mywin.mouseVisible = False

    fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0, 0], sf=0)

    # saving trial information for output
    responses: List[str] = []

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
        stimuli = "code" if trials["codeorprose"].iloc[ii] == 0 else "prose"
        if stimuli == "code":
            # TODO
            pass
        elif stimuli == "prose":
            # TODO
            pass

        # TODO
        responses.append("response")

    # save the behavioural data into matlab file
    directory = get_recording_dir(eeg.board_name, "visual-codeprose", subject, session)
    fn = f"subject{subject}_session{session}_behOutput_{strftime('%Y-%m-%d-%H.%M.%S', gmtime())}.csv"

    output = np.array(responses)
    df = pd.DataFrame(output)
    df.save_csv(directory / fn)

    # Overall Accuracy
    # TODO: Actually measure accuracy
    print("Overall Mean Accuracy = " + str(round(100 * np.mean(output[:, 6]))))

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
    raise NotImplementedError


def instructions():
    raise NotImplementedError
