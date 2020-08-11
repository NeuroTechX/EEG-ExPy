import numpy as np
import socket
import platform


# Default channel names for the various brainflow devices.
EEG_CHANNELS = {
    'cyton' : [
        'Fp1', 'Fp2', 'C3', 'C4', 'P7', 'P8', 'O1', 'O2',
    ],
    'cyton_daisy' : [
        'Fp1', 'Fp2', 'C3', 'C4', 'P7', 'P8', 'O1', 'O2',
        'F7' , 'F8' , 'F3', 'F4', 'T7', 'T8', 'P3', 'P4',
    ],
    'brainbit' : [
        'T3', 'T4', 'O1', 'O2'
    ],
    'unicorn' : [
        'Fz', 'C3', 'Cz', 'C4', 'Pz', 'PO7', 'Oz', 'PO8'
    ],
    'synthetic':[
        'T7', 'CP5', 'FC5', 'C3', 'C4', 'FC6', 'CP6', 'T8'
    ]
}

BRAINFLOW_CHANNELS = {
    'cyton': EEG_CHANNELS['cyton'] + ['accel_0', 'accel_1', 'accel_2'],
    'cyton_daisy': EEG_CHANNELS['cyton_daisy'] + ['accel_0', 'accel_1', 'accel_2'],
    'synthetic': EEG_CHANNELS['synthetic'],
}

CHANNEL_INDICES = {
    'muse2016': [0, 1, 2, 3],
    'muse': [0, 1, 2, 3],
    'cyton': [0, 1, 2, 3, 4, 5, 6, 7],
    'cyton_daisy': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    'brainbit': [],

}

STIM_INDICES = {
    'muse2016': 5,
    'muse2': 4,
    'cyton': 11,
    'cyton_daisy': 19,
}

SAMPLE_FREQS = {
    'muse2016': 256,
    'muse2': 256,
    'cyton': 256,
    'cyton_daisy': 128
}

def get_openbci_ip(address, port):
    """ Gets the default IP address for connecting to the OpenBCI wifi shield but also allows
    users to pass their own values to override the defaults.

    Parameters:
        address (str): ip address
        port (str or int): ip port
    """
    if address == None:
        address = '192.168.4.1'

    if port == None:
        s = socket.socket()
        s.bind(('', 0))
        port = s.getsockname()[1]

    return address, port

def get_openbci_usb():
    if platform.system() == 'Linux':
        return '/dev/ttyUSB0'
    elif platform.system() == 'Windows':
        return 'COM3'
    elif platform.system() == 'Darwin':
        return input("Please enter USb port for Mac OS")

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