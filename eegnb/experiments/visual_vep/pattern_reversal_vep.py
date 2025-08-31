from time import time
import numpy as np

from psychopy import visual
from typing import Optional, Dict, Any
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

    def load_stimulus(self) -> Dict[str, Any]:
        # Frame rate, in Hz
        # GetActualFrameRate() crashes in psychxr due to 'EndFrame called before BeginFrame'
        actual_frame_rate = np.round(self.window.displayRefreshRate if self.use_vr else self.window.getActualFrameRate())
        # Ensure the expected frame rate matches and is divisable by the stimulus rate(soa)
        assert actual_frame_rate % self.soa == 0, f"Expected frame rate divisable by stimulus rate: {self.soa}, but got {actual_frame_rate} Hz"
        assert self.display_refresh_rate == actual_frame_rate, f"Expected frame rate {self.display_refresh_rate} Hz, but got {actual_frame_rate} Hz"

        if self.use_vr:
            # Create the VR checkerboard
            create_checkerboard = self.create_vr_checkerboard
            # the window is large over the eye, checkerboard should only cover the central vision
            size = self.window.size / 1.5
        else:
            # Create the Monitor checkerboard
            create_checkerboard = self.create_monitor_checkerboard
            size = (self.window_size[1], self.window_size[1])

        # The surrounding / periphery needs to be dark when not using vr.
        # Also used for covering eye which is not being stimulated.
        self.black_background = visual.Rect(self.window,
                                            width=self.window.size[0],
                                            height=self.window.size[1],
                                            fillColor='black')

        # A grey background behind the checkerboard must be used in vr to maintain luminence.
        self.grey_background = visual.Rect(self.window,
                                            width=self.window.size[0],
                                            height=self.window.size[1],
                                            fillColor=[-0.22, -0.22, -0.22])

        # Create checkerboard stimuli
        def create_checkerboard_stim(intensity_checks, pos):
            return visual.ImageStim(self.window,
                                    image=create_checkerboard(intensity_checks)['img'],
                                    units='pix', size=size, color='white', pos=pos)

        # Create fixation stimuli
        def create_fixation_stim(pos):
            fixation = visual.GratingStim(
                win=self.window, 
                pos=pos, 
                sf=400 if self.use_vr else 0.2,
                color=[1, 0, 0]
            )
            fixation.size = 0.02 if self.use_vr else 0.4
            return fixation

        # Create VR block instruction stimuli
        def create_vr_block_instruction(pos):
            return visual.TextStim(win=self.window, text="Focus on the red dot, and try not to blink whilst the squares are flashing, press the spacebar or pull the controller trigger when ready to commence.", color=[-1, -1, -1],
            pos=pos, height=0.1)

        # Create and position stimulus
        def create_eye_stimuli(eye_x_pos, pix_x_pos):
            return {
                'checkerboards': [
                    create_checkerboard_stim((1, -1), pos=(pix_x_pos, 0)),
                    create_checkerboard_stim((-1, 1), pos=(pix_x_pos, 0))
                ],
                'fixation': create_fixation_stim([eye_x_pos, 0]),
                'vr_block_instructions': create_vr_block_instruction((eye_x_pos, 0))
            }

        # Structure all stimuli in organized dictionary
        if self.use_vr:
            # Calculate pixel positions for stereoscopic presentation
            window_width = self.window.size[0]
            left_pix_x_pos = self.left_eye_x_pos * (window_width / 2)
            right_pix_x_pos = self.right_eye_x_pos * (window_width / 2)

            return {
                'left': create_eye_stimuli(self.left_eye_x_pos, left_pix_x_pos),
                'right': create_eye_stimuli(self.right_eye_x_pos, right_pix_x_pos)
            }
        else:
            return {
                'monoscopic': create_eye_stimuli(0, 0)
            }

    def _present_vr_block_instructions(self, open_eye, closed_eye):
        self.window.setBuffer(open_eye)
        self.stim[open_eye]['vr_block_instructions'].draw()
        self.stim[open_eye]['fixation'].draw()
        self.window.setBuffer(closed_eye)
        self.black_background.draw()

    def present_block_instructions(self, current_block: int) -> None:
        if self.use_vr:
            if current_block % 2 == 0:
                self._present_vr_block_instructions(open_eye="left", closed_eye="right")
            else:
                self._present_vr_block_instructions(open_eye="right", closed_eye="left")
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
            self.stim['monoscopic']['fixation'].draw()
        self.window.flip()

    def present_stimulus(self, idx: int):
        # Get the label of the trial
        trial_idx = self.current_block_index * self.block_trial_size + idx
        label = self.parameter[trial_idx]

        open_eye = 'left' if label == 0 else 'right'
        closed_eye = 'left' if label == 1 else 'right'

        # draw checkerboard and fixation
        if self.use_vr:
            self.window.setBuffer(open_eye)
            self.grey_background.draw()
            display = self.stim['left' if label == 0 else 'right']
        else:
            self.black_background.draw()
            display = self.stim['monoscopic']
            
        checkerboard_frame = idx % 2
        display['checkerboards'][checkerboard_frame].draw()
        display['fixation'].draw()

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
