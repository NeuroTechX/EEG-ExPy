""" eeg-notebooks/eegnb/experiments/visual_emfl/emfl.py """

import os
from glob import glob
from random import choice
from time import time
from typing import Optional

from psychopy import core, event, visual

from eegnb.devices.eeg import EEG
from eegnb.experiments import Experiment


class VisualEMFL(Experiment.BaseExperiment):
    """
    Efficient Multifunction Localizer (EMFL) for EEG-ExPy.
    Based on Marvi/Kanwisher Lab (2025).
    Uses a series of multitask movie clips to localize 14+ regions.
    """

    def __init__(self, duration=840, eeg: Optional[EEG]=None, save_fn=None,
                 n_trials=None, iti=0.0, soa=18.0, jitter=0.0, use_vr=False,
                 stim_dir=None):

        exp_name = "Efficient Multifunction Localizer"
        self.stim_dir = stim_dir or "/Users/mhough/Workspace/EEG-ExPy/eegnb/stimuli/visual/emfl"

        # 14 minute run (840s). Blocks are ~18-20s.
        if n_trials is None:
            n_trials = int(duration / soa)

        super(VisualEMFL, self).__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr)

    def load_stimulus(self):
        """
        Loads the EMFL movie blocks.
        """
        self.movie_files = glob(os.path.join(self.stim_dir, "*.mp4"))
        print(f"Loaded {len(self.movie_files)} EMFL block movies.")
        return self.movie_files

    def present_stimulus(self, idx: int, trial):
        """
        Presents one EMFL block (movie clip).
        """
        movie_path = choice(self.movie_files)
        mov = visual.MovieStim3(self.window, movie_path, size=(12, 12), flipVert=False)

        if self.eeg:
            # Marker identifies which specific block movie is playing
            block_id = int(os.path.basename(movie_path).split('_')[1].replace('block', ''))
            self.eeg.push_sample(marker=block_id, timestamp=time())

        start_time = core.getTime()
        while mov.status != visual.FINISHED and (core.getTime() - start_time < self.soa):
            mov.draw()
            self.window.flip()
            if 'escape' in event.getKeys():
                core.quit()
        mov.stop()
