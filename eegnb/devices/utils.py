import numpy as np
import socket
import platform

from brainflow import BoardShim, BoardIds


# Default channel names for the various brainflow devices.
EEG_CHANNELS = {
    'ganglion': ['fp1', 'fp2', 'tp7', 'tp8'],
    'cyton': BoardShim.get_eeg_names(BoardIds.CYTON_BOARD.value),
    'cyton_daisy': BoardShim.get_eeg_names(BoardIds.CYTON_DAISY_BOARD.value),
    'brainbit': BoardShim.get_eeg_names(BoardIds.BRAINBIT_BOARD.value),
    'unicorn': BoardShim.get_eeg_names(BoardIds.UNICORN_BOARD.value),
    'synthetic': BoardShim.get_eeg_names(BoardIds.SYNTHETIC_BOARD.value),
    'notion1': BoardShim.get_eeg_names(BoardIds.NOTION_1_BOARD.value),
    'notion2': BoardShim.get_eeg_names(BoardIds.NOTION_2_BOARD.value),
}

BRAINFLOW_CHANNELS = {
    'ganglion': [],
    'cyton': EEG_CHANNELS['cyton'] + ['accel_0', 'accel_1', 'accel_2'],
    'cyton_daisy': EEG_CHANNELS['cyton_daisy'] + ['accel_0', 'accel_1', 'accel_2'],
    'synthetic': EEG_CHANNELS['synthetic'],
}

EEG_INDICES = {
    'muse2016': [1, 2, 3, 4],
    'muse2': [1, 2, 3, 4],
    'museS', [1,2,3,4],
    'ganglion': BoardShim.get_eeg_channels(BoardIds.GANGLION_BOARD.value),
    'cyton': BoardShim.get_eeg_channels(BoardIds.CYTON_BOARD.value),
    'cyton_daisy': BoardShim.get_eeg_channels(BoardIds.CYTON_DAISY_BOARD.value),
    'brainbit': BoardShim.get_eeg_channels(BoardIds.BRAINBIT_BOARD.value),
    'unicorn': BoardShim.get_eeg_channels(BoardIds.UNICORN_BOARD.value),
    'synthetic': BoardShim.get_eeg_channels(BoardIds.SYNTHETIC_BOARD.value),
    'notion1': BoardShim.get_eeg_channels(BoardIds.NOTION_1_BOARD.value),
    'notion2': BoardShim.get_eeg_channels(BoardIds.NOTION_2_BOARD.value),
}

SAMPLE_FREQS = {
    'muse2016': 256,
    'muse2': 256,
    'museS': 256,
    'ganglion': BoardShim.get_sampling_rate(BoardIds.GANGLION_BOARD.value),
    'cyton': BoardShim.get_sampling_rate(BoardIds.CYTON_BOARD.value),
    'cyton_daisy': BoardShim.get_sampling_rate(BoardIds.CYTON_DAISY_BOARD.value),
    'brainbit': BoardShim.get_sampling_rate(BoardIds.BRAINBIT_BOARD.value),
    'unicorn': BoardShim.get_sampling_rate(BoardIds.UNICORN_BOARD.value),
    'synthetic': BoardShim.get_sampling_rate(BoardIds.SYNTHETIC_BOARD.value),
    'notion1': BoardShim.get_sampling_rate(BoardIds.NOTION_1_BOARD.value),
    'notion2': BoardShim.get_sampling_rate(BoardIds.NOTION_2_BOARD.value),
}

def get_openbci_usb():
    if platform.system() == 'Linux':
        return '/dev/ttyUSB0'
    elif platform.system() == 'Windows':
        return input('Please enter USB port for Windows: ')
    elif platform.system() == 'Darwin':
        return input("Please enter USB port for Mac OS: ")

def create_stim_array(timestamps, markers):
    """ Creates a stim array which is the lenmgth of the EEG data where the stimuli are lined up
    with their corresponding EEG sample.

    Parameters:
        timestamps (array of floats): Timestamps from the EEG data.
        markers (array of ints): Markers and their associated timestamps.
        """
    num_samples = len(timestamps)
    stim_array = np.zeros((num_samples, 1))
    for marker in markers:
        stim_idx = np.where(timestamps == marker[1])
        stim_array[stim_idx] = marker[0]

    return stim_array
