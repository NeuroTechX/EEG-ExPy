from .base import EEGDevice
from .muse import MuseDevice
from ._brainflow import BrainflowDevice

all_devices = MuseDevice.devices + BrainflowDevice.devices
