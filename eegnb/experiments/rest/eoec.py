
from typing import Optional
from time import time

from psychopy import prefs

prefs.hardware["audioLib"] = "PTB"
prefs.hardware["audioLatencyMode"] = 3

from psychopy import sound, visual
from pylsl import StreamInfo, StreamOutlet

try:  # pyserial is optional
    import serial
except Exception:  # pragma: no cover - handled gracefully
    serial = None

import numpy as np
from pandas import DataFrame

from eegnb.devices.eeg import EEG
from eegnb.experiments import Experiment


class RestEyesOpenCloseAlternating(Experiment.BaseExperiment):
    """
    Resting-state experiment with alternating eyes-open / eyes-closed blocks, 
    and minimal visual and auditory cues to assist with task instructions.
    """

    def __init__(
        self,
        duration: Optional[float] = None,
        eeg: Optional[EEG] = None,
        save_fn: Optional[str] = None,
        block_duration: float = 60.0,
        n_cycles: int = 5,
        serial_port: Optional[str] = None,
        use_verbal_cues: bool = False,
        open_audio: Optional[str] = None,
        close_audio: Optional[str] = None
        ):

        exp_name = "Rest Eyes Open/Closed Alternating"
        if duration is None:
            duration = block_duration * 2 * n_cycles
        self.block_duration = block_duration
        self.n_cycles = n_cycles
        self.serial_port = serial_port
        self.use_verbal_cues = use_verbal_cues
        self.open_audio = open_audio
        self.close_audio = close_audio
        self.serial = None
        self.outlet = None
        self.open_sound = None
        self.close_sound = None
        super().__init__(
            exp_name,
            duration,
            eeg,
            save_fn,
            n_trials=2 * n_cycles,
            iti=0,
            soa=block_duration,
            jitter=0,
        )


    def load_stimulus(self):
        self.fixation = visual.TextStim(win=self.window, text="+", height=1.0)
        self.close_text = visual.TextStim(win=self.window, text="Close your eyes", height=1.0)
        return [self.fixation, self.close_text]


    def setup(self, instructions: bool = True):
        # recompute number of trials if duration was changed after init
        self.n_cycles = max(1, int(self.duration // (2 * self.block_duration)))
        self.n_trials = self.n_cycles * 2
        super().setup(instructions)

        # overwrite trial sequence to alternate between open (0) and closed (1)
        parameter = np.tile([0, 1], self.n_cycles)
        self.trials = DataFrame(
            dict(parameter=parameter, timestamp=np.zeros(self.n_trials))
        )

        # LSL outlet for markers
        info = StreamInfo("Markers", "Markers", 1, 0, "int32", "eyeclosure-baseline")
        self.outlet = StreamOutlet(info)

        # serial connection for hardware triggers
        if self.serial_port and serial is not None:
            try:
                self.serial = serial.Serial(self.serial_port, 115200, timeout=1)
            except Exception:  # pragma: no cover
                self.serial = None

        # sounds for block transitions
        if self.use_verbal_cues and self.open_audio and self.close_audio:
            self.open_sound = sound.Sound(self.open_audio)
            self.close_sound = sound.Sound(self.close_audio)
        else:
            self.open_sound = sound.Sound(440, secs=0.2)
            self.close_sound = sound.Sound(330, secs=0.2)


    def present_stimulus(self, idx: int):
        if self.outlet is None or self.open_sound is None or self.close_sound is None:
            raise RuntimeError("setup() must be called before present_stimulus()")

        label = self.trials["parameter"].iloc[idx]  # 0 open, 1 closed
        if self.trials["timestamp"].iloc[idx] == 0:
            timestamp = time()
            self.trials.at[idx, "timestamp"] = timestamp
            self.outlet.push_sample([self.markernames[label]], timestamp)
            if self.eeg:
                marker = (
                    [self.markernames[label]]
                    if self.eeg.backend == "muselsl"
                    else self.markernames[label]
                )
                self.eeg.push_sample(marker=marker, timestamp=timestamp)
            if self.serial:
                try:
                    self.serial.write(bytes([self.markernames[label]]))
                except Exception:  # pragma: no cover
                    pass
            if label == 0:
                self.open_sound.play()
            else:
                self.close_sound.play()

        if label == 0:
            self.fixation.draw()
        else:
            self.close_text.draw()
        self.window.flip()

    def run(self, instructions: bool = True):
        try:
            super().run(instructions)
        finally:
            if self.serial:
                self.serial.close()



