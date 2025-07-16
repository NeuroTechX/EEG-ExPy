from time import time

from psychopy import visual
from typing import Optional, Any, List
from eegnb.devices.eeg import EEG
from eegnb.experiments import Experiment
from stimupy.stimuli.checkerboards import contrast_contrast


class VisualPatternReversalVEP(Experiment.BaseExperiment):

    def __init__(self, duration=120, eeg: Optional[EEG] = None, save_fn=None,
                 n_trials=2000, iti=0, soa=0.5, jitter=0, use_vr=False, use_fullscr=True):

        self.black_background = None
        self.stim = None
        exp_name = "Visual Pattern Reversal VEP"
        super().__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr, use_fullscr)

    @staticmethod
    def create_monitor_checkerboard(intensity_checks):
        # Standard parameters for monitor-based pattern reversal VEP
        # Using standard 1 degree check size at 30 pixels per degree
        return contrast_contrast(
            visual_size=(16, 16),  # aspect ratio in degrees
            ppd=72,  # pixels per degree
            frequency=(0.5, 0.5),  # spatial frequency of the checkerboard (0.5 cpd = 1 degree check size)
            intensity_checks=intensity_checks,
            target_shape=(1, 1),
            alpha=0,
            tau=0
        )

    @staticmethod
    def create_vr_checkerboard(intensity_checks):
        # Optimized parameters for Oculus/Meta Quest 2 with PC link
        # Quest 2 has approximately 20 pixels per degree and a ~90° FOV
        # Using standard 1 degree check size (0.5 cpd)
        return contrast_contrast(
            visual_size=(20, 20),  # size in degrees - covers a good portion of the FOV
            ppd=20,  # pixels per degree for Quest 2
            frequency=(0.5, 0.5),  # spatial frequency (0.5 cpd = 1 degree check size)
            intensity_checks=intensity_checks,
            target_shape=(1, 1),
            alpha=0,
            tau=0
        )

    def load_stimulus(self):
        if self.use_vr:
            # Create VR checkerboard
            create_checkerboard = self.create_vr_checkerboard

        else:
            # Create Monitor checkerboard
            create_checkerboard = self.create_monitor_checkerboard

        if self.use_vr:
            # the window is large over the eye, checkerboard should only cover the central vision
            size = self.window.size / 1.5
        else:
            size = (self.window_size[1], self.window_size[1])

        # the surrounding / periphery needs to be dark
        self.black_background = visual.Rect(self.window,
                                            width=self.window.size[0],
                                            height=self.window.size[1],
                                            fillColor='black')

        def create_checkerboard_stim(intensity_checks):
            return visual.ImageStim(self.window,
                                    image=create_checkerboard(intensity_checks)['img'],
                                    units='pix', size=size, color='white')

        self.stim = [create_checkerboard_stim((1, -1)), create_checkerboard_stim((-1, 1))]

    def present_stimulus(self, idx: int):
        self.black_background.draw()

        # draw checkerboard
        checkerboard_frame = idx % 2
        image = self.stim[checkerboard_frame]
        image.draw()
        self.window.flip()

        # Pushing the sample to the EEG
        self.eeg.push_sample(marker=checkerboard_frame + 1, timestamp=time())

    def present_iti(self):
        self.black_background.draw()
        self.window.flip()
