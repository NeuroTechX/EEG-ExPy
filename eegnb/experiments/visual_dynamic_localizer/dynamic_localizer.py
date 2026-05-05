""" eeg-notebooks/eegnb/experiments/visual_dynamic_localizer/dynamic_localizer.py """

import os
from glob import glob
from random import choice
from time import time
from typing import Optional

import numpy as np
from psychopy import core, event, visual

from eegnb.devices.eeg import EEG
from eegnb.experiments import Experiment


class VisualDynamicLocalizer(Experiment.BaseExperiment):
    """
    Pitcher/Kanwisher Dynamic Localizer for EEG-ExPy.
    Uses video clips (3s) in a block design (18s/block).
    Supports Faces, Bodies, Scenes, Objects, and Scrambled.
    """

    def __init__(self, duration=234, eeg: Optional[EEG]=None, save_fn=None,
                 n_trials=None, iti=0.0, soa=18.0, jitter=0.0, use_vr=False,
                 stim_dir=None, categories=['faces', 'scenes', 'bodies', 'objects']):

        exp_name = "Dynamic Localizer"
        self.categories = categories
        self.stim_dir = stim_dir or "/Users/mhough/Workspace/EEG-ExPy/eegnb/stimuli/visual/dynamic_localizer"

        # 18s blocks * n_blocks. Standard is ~12-14 blocks.
        if n_trials is None:
            n_trials = int(duration / soa)

        super(VisualDynamicLocalizer, self).__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr)

    def load_stimulus(self):
        """
        Organizes video files by category.
        """
        self.stim_dict = {}
        for cat in self.categories:
            cat_path = os.path.join(self.stim_dir, cat)
            files = glob(os.path.join(cat_path, "*.mp4"))
            if files:
                self.stim_dict[cat] = files
                print(f"Loaded {len(files)} videos for category: {cat}")
            else:
                print(f"Warning: No videos found for {cat} in {cat_path}")

        return list(self.categories)

    def present_stimulus(self, idx: int, trial):
        """
        Presents one 18s block of video clips.
        Each block consists of 6 clips (3s each).
        """
        cat_idx = self.trials["parameter"].iloc[idx]
        category = self.categories[cat_idx]

        if category not in self.stim_dict:
            print(f"Skipping block: No stimuli for {category}")
            core.wait(self.soa)
            return

        # Pick 6 clips for this block
        clips = [choice(self.stim_dict[category]) for _ in range(6)]

        # 1-back task logic: occasionally repeat a clip
        if np.random.random() < 0.2:
            repeat_idx = np.random.randint(1, 6)
            clips[repeat_idx] = clips[repeat_idx-1]
            marker_val = 200 + cat_idx # Task trial
        else:
            marker_val = 100 + cat_idx # Normal block

        # Pushing the sample to the EEG at block onset
        if self.eeg:
            self.eeg.push_sample(marker=marker_val, timestamp=time())

        # Play the clips
        for clip_path in clips:
            mov = visual.MovieStim3(self.window, clip_path, size=(10, 10), flipVert=False)
            start_time = core.getTime()
            while mov.status != visual.FINISHED and (core.getTime() - start_time < 3.0):
                mov.draw()
                self.window.flip()
                if 'escape' in event.getKeys():
                    core.quit()
            mov.stop()
