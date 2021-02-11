"""
An experiment to see if one can distinguish between reading code vs prose using EEG.

 - Original fMRI study:
     https://ieeexplore.ieee.org/abstract/document/7985660
 - Replication study by Fucci et al, using 1-channel EEG as well as skin-, and heart-related signals.
     https://arxiv.org/abs/1903.03426
"""

from time import time, strftime, gmtime
from typing import List
from pathlib import Path
from dataclasses import dataclass, field
from ...devices.eeg import EEG

import numpy as np
import pandas as pd
from psychopy import visual, core, event

from eegnb import get_recording_dir


@dataclass
class ExperimentSpec:
    # TODO: Move and reuse this class in more experiments, as per https://github.com/NeuroTechX/eeg-notebooks/issues/76
    experiment_name: str
    eeg_device: EEG
    subject: int
    session: int
    params: dict = field(default_factory=dict)

    @property
    def output_dir(self) -> Path:
        return Path(
            get_recording_dir(
                self.eeg_device.device_name,
                "visual-codeprose",
                self.subject,
                self.session,
            )
        )


# 1 - Code
# 2 - Prose
cue_markernames = [1, 2]


# TODO: These default values are bad, they should be passed down correctly
def present(duration: int, eeg: EEG, subject=0, session=0, **kwargs) -> None:
    spec = ExperimentSpec("visual_codeprose", eeg, subject, session)

    # record_duration = np.float32(duration)

    # graphics
    window = visual.Window(
        [1440, 900], monitor="testMonitor", units="deg", fullscr=True
    )
    window.mouseVisible = False

    instruct = 1
    practicing = 1

    # Instructions function below
    # TODO: Implement instructions and practice
    if instruct:
        instructions(window)
    if practicing:
        practice(window)

    # Run the experiment
    df = run(window, n_trials=5)

    # save the behavioural data into CSV file
    fn = f"subject{subject}_session{session}_behOutput_{strftime('%Y-%m-%d-%H.%M.%S', gmtime())}.csv"
    df.to_csv(spec.output_dir / fn)

    # Overall Accuracy
    # TODO: Actually measure accuracy
    # print("Overall Mean Accuracy = " + str(round(100 * np.mean(output[:, 6]))))

    window.mouseVisible = True

    goodbye(window)

    # Cleanup
    window.close()


def run(window: visual.Window, n_trials: int) -> pd.DataFrame:
    # Setup log
    codeorprose = np.random.binomial(1, 0.5, n_trials)

    trials = pd.DataFrame(dict(codeorprose=codeorprose))

    # Get ready screen
    text = visual.TextStim(
        win=window,
        text="find the arrow keys, and begin fixating now. the first trial is about to begin",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    text.draw()

    fixation = visual.GratingStim(win=window, size=0.2, pos=[0, 0], sf=0)
    fixation.draw()

    window.flip()
    core.wait(1)

    # TODO: Make sure clocks are handled correctly
    # create a clock for rt's
    clock = core.Clock()
    # create a timer for the experiment and EEG markers
    start = time()

    # TODO: Place somewhere reasonable, figure out how to distribute with eegnb?
    img_path = Path("/home/erb/Skola/Exjobb/other/2016-materials/materials.final/")
    assert img_path.exists()

    code_imgs = (img_path / "comp").glob("*.png")
    prose_imgs = (img_path / "prose/bugs").glob("*.PNG")

    # saving trial information for output
    responses: List[dict] = []

    for ii, trial in trials.iterrows():
        stimuli = "code" if trials["codeorprose"].iloc[ii] == 0 else "prose"
        print(f"Trial {ii} with stimuli {stimuli}")
        try:
            image_path = next(code_imgs) if stimuli == "code" else next(prose_imgs)
        except StopIteration:
            # TODO: Do something more reasonable if we run out of images
            break

        image = visual.ImageStim(win=window, image=image_path)
        image.draw()

        window.flip()
        t_presented = clock.getTime()

        core.wait(0.1)
        keys = event.waitKeys(keyList=["left", "right"], timeStamped=clock)
        print(keys)
        t_answered = clock.getTime()

        response = True if keys[0][0] == "right" else False

        # TODO
        responses.append(
            {
                "stimuli": stimuli,
                "image": image,
                "response": response,
                "t_presented": t_presented,
                "t_answered": t_answered,
            }
        )

    return pd.DataFrame(responses)


def goodbye(window):
    # Goodbye Screen
    text = visual.TextStim(
        win=window,
        text="Thank you for participating. Press spacebar to exit the experiment.",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    text.draw()
    window.flip()
    event.waitKeys(keyList="space")


def practice(window):
    text = visual.TextStim(
        win=window,
        text="Practice not implemented yet.\n\nPress space to continue.",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    text.draw()
    window.flip()

    event.waitKeys(keyList="space")


def instructions(window):
    # TODO: Add instructions
    # TODO: Check that instructions are the same as in original studies
    text = visual.TextStim(
        win=window,
        text="We will show you alternating images of code or prose, and it is your task to answer questions about the problems presented.\n\nPress space to continue.",
        color=[-1, -1, -1],
        pos=[0, 5],
    )
    text.draw()
    window.flip()

    text = visual.TextStim(
        win=window,
        text="To answer 'correct' on a problem, press the right (>) arrow key.\nTo answer 'false', press the left (<) arrow key.\n\nPress space to continue.",
    )
    text.draw()
    window.flip()

    event.waitKeys(keyList="space")
