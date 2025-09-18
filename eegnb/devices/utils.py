import numpy as np
import socket
import platform
import serial

from brainflow.board_shim import BoardShim, BoardIds


# Default channel names for the various EEG devices.
EEG_CHANNELS = {
    "muse2016": ["TP9", "AF7", "AF8", "TP10", "Right AUX"],
    "muse2": ["TP9", "AF7", "AF8", "TP10", "Right AUX"],
    "museS": ["TP9", "AF7", "AF8", "TP10", "Right AUX"],
    "muse2016_bfn": BoardShim.get_eeg_names(BoardIds.MUSE_2016_BOARD.value),
    "muse2016_bfb": BoardShim.get_eeg_names(BoardIds.MUSE_2016_BLED_BOARD.value),
    "muse2_bfn": BoardShim.get_eeg_names(BoardIds.MUSE_2_BOARD.value),
    "muse2_bfb": BoardShim.get_eeg_names(BoardIds.MUSE_2_BLED_BOARD.value),
    "museS_bfn": BoardShim.get_eeg_names(BoardIds.MUSE_S_BOARD.value),
    "museS_bfb": BoardShim.get_eeg_names(BoardIds.MUSE_S_BLED_BOARD.value),
    "ganglion": ["fp1", "fp2", "tp7", "tp8"],
    "cyton": BoardShim.get_eeg_names(BoardIds.CYTON_BOARD.value),
    "cyton_daisy": BoardShim.get_eeg_names(BoardIds.CYTON_DAISY_BOARD.value),
    "brainbit": BoardShim.get_eeg_names(BoardIds.BRAINBIT_BOARD.value),
    "unicorn": BoardShim.get_eeg_names(BoardIds.UNICORN_BOARD.value),
    "synthetic": BoardShim.get_eeg_names(BoardIds.SYNTHETIC_BOARD.value),
    "notion1": BoardShim.get_eeg_names(BoardIds.NOTION_1_BOARD.value),
    "notion2": BoardShim.get_eeg_names(BoardIds.NOTION_2_BOARD.value),
    "crown": BoardShim.get_eeg_names(BoardIds.CROWN_BOARD.value),
    "freeeeg32": [f"eeg_{i}" for i in range(0, 32)],
}

BRAINFLOW_CHANNELS = {
    "ganglion": [],
    "cyton": EEG_CHANNELS["cyton"] + ["accel_0", "accel_1", "accel_2"],
    "cyton_daisy": EEG_CHANNELS["cyton_daisy"] + ["accel_0", "accel_1", "accel_2"],
    "synthetic": EEG_CHANNELS["synthetic"],
}

EEG_INDICES = {
    "muse2016": [1, 2, 3, 4],
    "muse2": [1, 2, 3, 4],
    "museS": [1, 2, 3, 4],
    "muse2016_bfn": BoardShim.get_eeg_channels(BoardIds.MUSE_2016_BOARD.value),
    "muse2016_bfb": BoardShim.get_eeg_channels(BoardIds.MUSE_2016_BLED_BOARD.value),
    "muse2_bfn": BoardShim.get_eeg_channels(BoardIds.MUSE_2_BOARD.value),
    "muse2_bfb": BoardShim.get_eeg_channels(BoardIds.MUSE_2_BLED_BOARD.value),
    "museS_bfn": BoardShim.get_eeg_channels(BoardIds.MUSE_S_BOARD.value),
    "museS_bfb": BoardShim.get_eeg_channels(BoardIds.MUSE_S_BLED_BOARD.value),
    "ganglion": BoardShim.get_eeg_channels(BoardIds.GANGLION_BOARD.value),
    "cyton": BoardShim.get_eeg_channels(BoardIds.CYTON_BOARD.value),
    "cyton_daisy": BoardShim.get_eeg_channels(BoardIds.CYTON_DAISY_BOARD.value),
    "brainbit": BoardShim.get_eeg_channels(BoardIds.BRAINBIT_BOARD.value),
    "unicorn": BoardShim.get_eeg_channels(BoardIds.UNICORN_BOARD.value),
    "synthetic": BoardShim.get_eeg_channels(BoardIds.SYNTHETIC_BOARD.value),
    "notion1": BoardShim.get_eeg_channels(BoardIds.NOTION_1_BOARD.value),
    "notion2": BoardShim.get_eeg_channels(BoardIds.NOTION_2_BOARD.value),
    "crown": BoardShim.get_eeg_channels(BoardIds.CROWN_BOARD.value),
    "freeeeg32": BoardShim.get_eeg_channels(BoardIds.FREEEEG32_BOARD.value),
}

SAMPLE_FREQS = {
    "muse2016": 256,
    "muse2": 256,
    "museS": 256,
    "muse2016_bfn": BoardShim.get_sampling_rate(BoardIds.MUSE_2016_BOARD.value),
    "muse2016_bfb": BoardShim.get_sampling_rate(BoardIds.MUSE_2016_BLED_BOARD.value),
    "muse2_bfn": BoardShim.get_sampling_rate(BoardIds.MUSE_2_BOARD.value),
    "muse2_bfb": BoardShim.get_sampling_rate(BoardIds.MUSE_2_BLED_BOARD.value),
    "museS_bfn": BoardShim.get_sampling_rate(BoardIds.MUSE_S_BOARD.value),
    "museS_bfb": BoardShim.get_sampling_rate(BoardIds.MUSE_S_BLED_BOARD.value),
    "ganglion": BoardShim.get_sampling_rate(BoardIds.GANGLION_BOARD.value),
    "cyton": BoardShim.get_sampling_rate(BoardIds.CYTON_BOARD.value),
    "cyton_daisy": BoardShim.get_sampling_rate(BoardIds.CYTON_DAISY_BOARD.value),
    "brainbit": BoardShim.get_sampling_rate(BoardIds.BRAINBIT_BOARD.value),
    "unicorn": BoardShim.get_sampling_rate(BoardIds.UNICORN_BOARD.value),
    "synthetic": BoardShim.get_sampling_rate(BoardIds.SYNTHETIC_BOARD.value),
    "notion1": BoardShim.get_sampling_rate(BoardIds.NOTION_1_BOARD.value),
    "notion2": BoardShim.get_sampling_rate(BoardIds.NOTION_2_BOARD.value),
    "crown": BoardShim.get_sampling_rate(BoardIds.CROWN_BOARD.value),
    "freeeeg32": BoardShim.get_sampling_rate(BoardIds.FREEEEG32_BOARD.value),
}


def create_stim_array(timestamps, markers):
    """Creates a stim array which is the lenmgth of the EEG data where the stimuli are lined up
    with their corresponding EEG sample.
    Parameters:
        timestamps (array of floats): Timestamps from the EEG data.
        markers (array of ints): Markers and their associated timestamps.
    """
    # marker_max = np.max(markers)
    num_samples = len(timestamps)
    stim_array = np.zeros((num_samples, 1))
    for marker in markers:
        stim_idx = np.where(timestamps == marker[1])
        stim_array[stim_idx] = marker[0]

    return stim_array


def get_openbci_usb():
    print("\nGetting a list of available serial ports...")
    port_list = serial_ports()
    i = 0
    for port in port_list:
        print(f"[{i}] {port}")
        i += 1
    port_number = input("Select Port(number): ")
    if port_number == "":
        return port_list[int(input("This field is required. Select Port(number): "))]
    else:
        return str(port_list[int(port_number)]).split(" - ")[0]


def serial_ports():
    return serial.tools.list_ports.comports()
