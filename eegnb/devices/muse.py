import sys
import logging
from time import time, sleep
from multiprocessing import Process
from typing import List, Optional

import numpy as np
import muselsl
import pylsl

from .base import EEGDevice, _check_samples

logger = logging.getLogger(__name__)

BACKEND = "bleak"
CHANNELS_MUSE = ["TP9", "AF7", "AF8", "TP10"]


def stream(address, sources):
    muselsl.stream(
        address,
        backend=BACKEND,
        ppg_enabled="PPG" in sources,
        acc_enabled="ACC" in sources,
        gyro_enabled="GYRO" in sources,
    )


def record(duration, filename, data_source="EEG"):
    muselsl.record(duration=duration, filename=filename, data_source=data_source)


class MuseDevice(EEGDevice):
    # list of muse devices
    devices = [
        "muse2016",
        "muse2",
        "museS",
    ]

    def __init__(self, device_name: str):
        EEGDevice.__init__(self, device_name)
        self.stream_process: Optional[Process] = None

    @property
    def started(self) -> bool:
        if self.stream_process:
            return self.stream_process.exitcode is None
        return False

    def start(self, filename: str = None, duration=None):
        """
        Starts the EEG device.

        Parameters:
            filename (str): name of the file to save the sessions data to.
        """
        sources = ["EEG"]  # + ["PPG", "ACC", "GYRO"]
        if not duration:
            duration = 300

        # Not sure why we only do this on *nix
        # Makes it seem like streaming is only supported on *nix?
        if not self.started and sys.platform in ["linux", "linux2", "darwin"]:
            # Look for muses
            muses = muselsl.list_muses(backend=BACKEND)
            # FIXME: fix upstream
            muses = [m for m in muses if m["name"].startswith("Muse")]
            if not muses:
                raise Exception("No Muses found")

            # self.muse = muses[0]

            # Start streaming process
            # daemon=False to ensure orderly shutdown/disconnection
            stream_process = Process(
                target=stream, args=(muses[0]["address"], sources), daemon=False
            )
            stream_process.start()
            self.stream_process = stream_process

        # Create markers stream outlet
        self.marker_outlet = pylsl.StreamOutlet(
            pylsl.StreamInfo("Markers", "Markers", 1, 0, "int32", "myuidw43536")
        )

        self.record(sources, duration, filename)

        # FIXME: What's the purpose of this? (Push sample indicating recording start?)
        self.push_sample([99], timestamp=time())

    def record(self, sources: List[str], duration, filename):
        # Start a background process that will stream data from the first available Muse
        for source in sources:
            logger.info("Starting background recording process")
            rec_process = Process(
                target=record, args=(duration, filename, source), daemon=True
            )
            rec_process.start()

    def stop(self):
        pass

    def push_sample(self, marker: List[int], timestamp: float):
        self.marker_outlet.push_sample(marker, timestamp)

    def _read_buffer(self) -> np.ndarray:
        from eegwatch.lslutils import _get_inlets

        inlets = _get_inlets(verbose=False)

        for i in range(5):
            for inlet in inlets:
                inlet.pull(timeout=0.5)  # type: ignore
            inlets = [inlet for inlet in inlets if inlet.buffer.any()]  # type: ignore
            if inlets:
                break
            else:
                logger.info("No inlets with data, trying again in a second...")
                sleep(1)

        if not inlets:
            raise Exception("No inlets found")

        inlet = inlets[0]
        return inlet.buffer  # type: ignore

    def check(self) -> List[str]:
        checked = _check_samples(
            self._read_buffer(), channels=["TP9", "AF7", "AF8", "TP10"]
        )
        bads = [ch for ch, ok in checked.items() if not ok]
        return bads
