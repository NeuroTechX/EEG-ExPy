from time import time
import numpy as np
from pandas import DataFrame

from psychopy import visual
from typing import Optional
from eegnb.devices.eeg import EEG
from eegnb.experiments.BlockExperiment import BlockExperiment
from stimupy.stimuli.checkerboards import contrast_contrast

QUEST_PPD = 20

class VisualPatternReversalVEP(BlockExperiment):

    def __init__(self, display_refresh_rate: int, eeg: Optional[EEG] = None, save_fn=None,
                 block_duration_seconds=50, block_trial_size: int=100, n_blocks: int=4, use_vr=False, use_fullscr=True):

        self.display_refresh_rate = display_refresh_rate
        soa=0.5
        iti=0
        jitter=0

        super().__init__("Visual Pattern Reversal VEP", block_duration_seconds, eeg, save_fn, block_trial_size, n_blocks, iti, soa, jitter, use_vr, use_fullscr, stereoscopic=True)

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
            ppd=QUEST_PPD,  # pixels per degree for Quest 2
            frequency=(0.5, 0.5),  # spatial frequency (0.5 cpd = 1 degree check size)
            intensity_checks=intensity_checks,
            target_shape=(0, 0),
            alpha=0,
            tau=0
        )

    def load_stimulus(self):
        # Frame rate, in Hz
        # GetActualFrameRate() crashes in psychxr due to 'EndFrame called before BeginFrame'
        actual_frame_rate = np.round(self.window.displayRefreshRate if self.use_vr else self.window.getActualFrameRate())
        # Ensure the expected frame rate matches and is divisable by the stimulus rate(soa)
        assert actual_frame_rate % self.soa == 0, f"Expected frame rate divisable by stimulus rate: {self.soa}, but got {actual_frame_rate} Hz"
        assert self.display_refresh_rate == actual_frame_rate, f"Expected frame rate {self.display_refresh_rate} Hz, but got {actual_frame_rate} Hz"


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

        # the surrounding / periphery needs to be dark when not vr.
        self.black_background = visual.Rect(self.window,
                                            width=self.window.size[0],
                                            height=self.window.size[1],
                                            fillColor='black')

        # a grey background must be used in vr to maintain luminence.
        self.grey_background = visual.Rect(self.window,
                                            width=self.window.size[0],
                                            height=self.window.size[1],
                                            fillColor=[-0.22, -0.22, -0.22])


        # fixation
        grating_sf = 400 if self.use_vr else 0.2
        self.fixation = visual.GratingStim(win=self.window, pos=[0, 0], sf=grating_sf, color=[1, 0, 0])
        self.fixation.size = 0.02 if self.use_vr else 0.4

        def create_checkerboard_stim(intensity_checks):
            return visual.ImageStim(self.window,
                                    image=create_checkerboard(intensity_checks)['img'],
                                    units='pix', size=size, color='white')

        return [create_checkerboard_stim((1, -1)), create_checkerboard_stim((-1, 1))]

    def _present_vr_block_instructions(self, open_eye, closed_eye, open_x):
        self.window.setBuffer(open_eye)
        text = visual.TextStim(win=self.window, text="Press spacebar or controller when ready.", color=[-1, -1, -1], pos=(open_x, 0))
        text.draw()
        self.fixation.pos = (open_x, 0)
        self.fixation.draw()
        self.window.setBuffer(closed_eye)
        self.grey_background.draw()

    def present_block_instructions(self, current_block: int) -> None:
        if self.use_vr:
            if current_block % 2 == 0:
                self._present_vr_block_instructions(open_eye="left", closed_eye="right", open_x=self.left_eye_x_pos)
            else:
                self._present_vr_block_instructions(open_eye="right", closed_eye="left", open_x=self.right_eye_x_pos)
        else:
            if current_block % 2 == 0:
                instruction_text = (
                    "Close your right eye, then focus on the red dot with your left eye. "
                    "Press spacebar or controller when ready."
                )
            else:
                instruction_text = (
                    "Close your left eye, then focus on the red dot with your right eye. "
                    "Press spacebar or controller when ready."
                )
            text = visual.TextStim(win=self.window, text=instruction_text, color=[-1, -1, -1])
            text.draw()
            self.fixation.draw()
        self.window.flip()

    def present_stimulus(self, idx: int):
        # Get the label of the trial
        block_trial_offset = self.current_block_index*self.block_trial_size
        label = self.trials["parameter"].iloc[idx+block_trial_offset]

        open_eye, open_x = ('left', self.left_eye_x_pos) if label == 0 else ('right', self.right_eye_x_pos)
        closed_eye, closed_x = ('left', self.left_eye_x_pos) if label == 1 else ('right', self.right_eye_x_pos)

        if self.use_vr:
            self.window.setBuffer(open_eye)
            self.grey_background.draw()
        else:
            self.black_background.draw()

        # draw checkerboard
        checkerboard_frame = idx % 2
        image = self.stim[checkerboard_frame]
        if self.stereoscopic:
            window_width = self.window.size[0]
            open_pix_x_pos = open_x * (window_width / 2)  # Convert norm to pixels
            image.pos = (open_pix_x_pos, 0)
        image.draw()
        self.fixation.pos = (open_x, 0)
        self.fixation.draw()

        if self.use_vr:
            self.window.setBuffer(closed_eye)
            self.black_background.draw()
        self.window.flip()

        # Pushing the sample to the EEG
        marker = self.markernames[label]
        self.eeg.push_sample(marker=marker, timestamp=time())

    def present_iti(self):
        if self.use_vr:
            for eye in ['left', 'right']:
                self.window.setBuffer(eye)
                self.black_background.draw()
        self.window.flip()
