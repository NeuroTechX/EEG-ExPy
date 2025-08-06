from time import time
import numpy as np
from pandas import DataFrame

from psychopy import visual
from typing import Optional
from eegnb.devices.eeg import EEG
from eegnb.experiments.BlockExperiment import BlockExperiment
from stimupy.stimuli.checkerboards import contrast_contrast


class VisualPatternReversalVEP(BlockExperiment):

    def __init__(self, eeg: Optional[EEG] = None, save_fn=None,
                 block_duration_seconds=50, block_trial_size: int=100, n_blocks: int=4, iti=0, soa=0.5, jitter=0,
                 use_vr=False, use_fullscr=True):

        super().__init__("Visual Pattern Reversal VEP", block_duration_seconds, eeg, save_fn, block_trial_size, n_blocks, iti, soa, jitter, use_vr, use_fullscr)

        self.instruction_text = f"""Welcome to the Visual Pattern Reversal VEP experiment!
        
        Stay still and focus on the red dot in the centre of the screen.
        
        This experiment will run for {n_blocks} blocks of {block_duration_seconds} seconds each.
        
        Press spacebar or controller to continue.
        """

        # Setting up the trial and parameter list
        left_eye = 0
        right_eye = 1
        # Alternate between left and right eye blocks
        block_eyes = []
        for block_num in range(n_blocks):
            eye = left_eye if block_num % 2 == 0 else right_eye
            block_eyes.extend([eye] * block_trial_size)
        self.parameter = np.array(block_eyes)
        self.trials = DataFrame(dict(parameter=self.parameter))


    @staticmethod
    def create_monitor_checkerboard(intensity_checks):
        # Standard parameters for monitor-based pattern reversal VEP
        # Using standard 1 degree check size at 30 pixels per degree
        return contrast_contrast(
            visual_size=(16, 16),  # aspect ratio in degrees
            ppd=72,  # pixels per degree
            frequency=(0.5, 0.5),  # spatial frequency of the checkerboard (0.5 cpd = 1 degree check size)
            intensity_checks=intensity_checks,
            target_shape=(0, 0),
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
            target_shape=(0, 0),
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

        # fixation
        grating_sf = 400 if self.use_vr else 0.2
        self.fixation = visual.GratingStim(win=self.window, pos=[0, 0], sf=grating_sf, color=[1, 0, 0])
        self.fixation.size = 0.02 if self.use_vr else 0.4

        def create_checkerboard_stim(intensity_checks):
            return visual.ImageStim(self.window,
                                    image=create_checkerboard(intensity_checks)['img'],
                                    units='pix', size=size, color='white')

        return [create_checkerboard_stim((1, -1)), create_checkerboard_stim((-1, 1))]

    def present_block_instructions(self, current_block):
        if current_block % 2 == 0:
            instruction_text = "Close your right eye, then focus on the red dot with your left eye. Press spacebar or controller when ready."
        else:
            instruction_text = "Close your left eye, then focus on the red dot with your right eye. Press spacebar or controller when ready."

        text = visual.TextStim(win=self.window, text=instruction_text, color=[-1, -1, -1])
        text.draw()
        self.fixation.draw()
        self.window.flip()

    def present_stimulus(self, idx: int):
        # Get the label of the trial
        block_trial_offset = self.current_block_index*self.block_trial_size
        label = self.trials["parameter"].iloc[idx+block_trial_offset]

        # eye for presentation
        eye = 'left' if label == 0 else 'right'

        self.black_background.draw()

        # draw checkerboard
        checkerboard_frame = idx % 2
        image = self.stim[checkerboard_frame]
        image.draw()
        self.fixation.draw()
        self.window.flip()

        # Pushing the sample to the EEG
        marker = self.markernames[label]
        self.eeg.push_sample(marker=marker, timestamp=time())

    def present_iti(self):
        self.black_background.draw()
        self.window.flip()
