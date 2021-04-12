"""
Abstraction for the various supported EEG devices.
"""

import logging
from typing import List, Dict
from abc import ABCMeta, abstractmethod

import numpy as np


logger = logging.getLogger(__name__)


def _check_samples(
    buffer: np.ndarray, channels: List[str], max_uv_abs=200
) -> Dict[str, bool]:
    # TODO: Better signal quality check
    chmax = dict(zip(channels, np.max(np.abs(buffer), axis=0)))
    return {ch: maxval < max_uv_abs for ch, maxval in chmax.items()}


def test_check_samples():
    buffer = np.array([[9.0, 11.0, -5, -13]])
    assert {"TP9": True, "AF7": False, "AF8": True, "TP10": False} == _check_samples(
        buffer, channels=["TP9", "AF7", "AF8", "TP10"], max_uv_abs=10
    )


class EEGDevice(metaclass=ABCMeta):
    def __init__(self, device: str) -> None:
        """
        The initialization function takes the name of the EEG device and initializes the appropriate backend.

        Parameters:
            device (str): name of eeg device used for reading data.
        """
        self.device_name = device

    @classmethod
    def create(cls, device_name: str, *args, **kwargs) -> "EEGDevice":
        from .muse import MuseDevice
        from ._brainflow import BrainflowDevice

        if device_name in BrainflowDevice.devices:
            return BrainflowDevice(device_name)
        elif device_name in MuseDevice.devices:
            return MuseDevice(device_name)
        else:
            raise ValueError(f"Invalid device name: {device_name}")

    def __enter__(self):
        self.start()

    def __exit__(self, *args):
        self.stop()

    @abstractmethod
    def start(self, filename: str = None, duration=None):
        """
        Starts the EEG device based on the defined backend.

        Parameters:
            filename (str): name of the file to save the sessions data to.
        """
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        raise NotImplementedError

    @abstractmethod
    def push_sample(self, marker: List[int], timestamp: float):
        """
        Push a marker and its timestamp to store alongside the EEG data.

        Parameters:
            marker (int): marker number for the stimuli being presented.
            timestamp (float): timestamp of stimulus onset from time.time() function.
        """
        raise NotImplementedError

    def get_samples(self):
        raise NotImplementedError

    @abstractmethod
    def check(self):
        raise NotImplementedError


def test_create():
    device = EEGDevice.create("synthetic")
    assert device
