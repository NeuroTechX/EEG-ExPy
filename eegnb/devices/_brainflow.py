import logging
from time import sleep
from multiprocessing import Process
from typing import List, Tuple

import numpy as np
import pandas as pd

from brainflow import BoardShim, BoardIds, BrainFlowInputParams
from .base import EEGDevice, _check_samples


logger = logging.getLogger(__name__)


class BrainflowDevice(EEGDevice):
    # list of brainflow devices
    devices: List[str] = [
        "ganglion",
        "ganglion_wifi",
        "cyton",
        "cyton_wifi",
        "cyton_daisy",
        "cyton_daisy_wifi",
        "brainbit",
        "unicorn",
        "synthetic",
        "brainbit",
        "notion1",
        "notion2",
    ]

    def __init__(
        self,
        device_name: str,
        serial_num=None,
        serial_port=None,
        mac_addr=None,
        other=None,
        ip_addr=None,
    ):
        EEGDevice.__init__(self, device_name)
        self.serial_num = serial_num
        self.serial_port = serial_port
        self.mac_address = mac_addr
        self.other = other
        self.ip_addr = ip_addr
        self.markers: List[Tuple[List[int], float]] = []
        self._init_brainflow()

    def start(self, filename: str = None, duration=None) -> None:
        self.save_fn = filename

        def record():
            sleep(duration)
            self._stop_brainflow()

        self.board.start_stream()
        if duration:
            logger.info(
                "Starting background recording process, will save to file: %s"
                % self.save_fn
            )
            self.recording = Process(target=lambda: record())
            self.recording.start()

    def stop(self) -> None:
        self._stop_brainflow()

    def push_sample(self, marker: List[int], timestamp: float):
        last_timestamp = self.board.get_current_board_data(1)[-1][0]
        self.markers.append((marker, last_timestamp))

    def check(self, max_uv_abs=200) -> List[str]:
        data = self.board.get_board_data()  # will clear board buffer
        # print(data)
        channel_names = BoardShim.get_eeg_names(self.brainflow_id)
        # FIXME: _check_samples expects different (Muse) inputs
        checked = _check_samples(data.T, channel_names, max_uv_abs=max_uv_abs)  # type: ignore
        bads = [ch for ch, ok in checked.items() if not ok]
        return bads

    def _init_brainflow(self) -> None:
        """
        This function initializes the brainflow backend based on the input device name. It calls
        a utility function to determine the appropriate USB port to use based on the current operating system.
        Additionally, the system allows for passing a serial number in the case that they want to use either
        the BrainBit or the Unicorn EEG devices from the brainflow family.

        Parameters:
             serial_num (str or int): serial number for either the BrainBit or Unicorn devices.
        """
        from eegnb.devices.utils import get_openbci_usb

        # Initialize brainflow parameters
        self.brainflow_params = BrainFlowInputParams()

        device_name_to_id = {
            "ganglion": BoardIds.GANGLION_BOARD.value,
            "ganglion_wifi": BoardIds.GANGLION_WIFI_BOARD.value,
            "cyton": BoardIds.CYTON_BOARD.value,
            "cyton_wifi": BoardIds.CYTON_WIFI_BOARD.value,
            "cyton_daisy": BoardIds.CYTON_DAISY_BOARD.value,
            "cyton_daisy_wifi": BoardIds.CYTON_DAISY_WIFI_BOARD.value,
            "brainbit": BoardIds.BRAINBIT_BOARD.value,
            "unicorn": BoardIds.UNICORN_BOARD.value,
            "callibri_eeg": BoardIds.CALLIBRI_EEG_BOARD.value,
            "notion1": BoardIds.NOTION_1_BOARD.value,
            "notion2": BoardIds.NOTION_2_BOARD.value,
            "synthetic": BoardIds.SYNTHETIC_BOARD.value,
        }

        # validate mapping
        assert all(name in device_name_to_id for name in self.devices)

        self.brainflow_id = device_name_to_id[self.device_name]

        if self.device_name == "ganglion":
            if self.serial_port is None:
                self.brainflow_params.serial_port = get_openbci_usb()
            # set mac address parameter in case
            if self.mac_address is None:
                logger.info(
                    "No MAC address provided, attempting to connect without one"
                )
            else:
                self.brainflow_params.mac_address = self.mac_address

        elif self.device_name in ["ganglion_wifi", "cyton_wifi", "cyton_daisy_wifi"]:
            if self.ip_addr is not None:
                self.brainflow_params.ip_address = self.ip_addr

        elif self.device_name in ["cyton", "cyton_daisy"]:
            if self.serial_port is None:
                self.brainflow_params.serial_port = get_openbci_usb()

        elif self.device_name == "callibri_eeg":
            if self.other:
                self.brainflow_params.other_info = str(self.other)

        # some devices allow for an optional serial number parameter for better connection
        if self.serial_num:
            self.brainflow_params.serial_number = str(self.serial_num)

        if self.serial_port:
            self.brainflow_params.serial_port = str(self.serial_port)

        # Initialize board_shim
        self.sfreq = BoardShim.get_sampling_rate(self.brainflow_id)
        self.board = BoardShim(self.brainflow_id, self.brainflow_params)
        self.board.prepare_session()

    def get_data(self) -> pd.DataFrame:
        from eegnb.devices.utils import create_stim_array

        data = self.board.get_board_data()  # will clear board buffer

        # transform data for saving
        data = data.T  # transpose data
        print(data)

        # get the channel names for EEG data
        if self.brainflow_id == BoardIds.GANGLION_BOARD.value:
            # if a ganglion is used, use recommended default EEG channel names
            ch_names = ["fp1", "fp2", "tp7", "tp8"]
        else:
            # otherwise select eeg channel names via brainflow API
            ch_names = BoardShim.get_eeg_names(self.brainflow_id)

        # pull EEG channel data via brainflow API
        eeg_data = data[:, BoardShim.get_eeg_channels(self.brainflow_id)]
        timestamps = data[:, BoardShim.get_timestamp_channel(self.brainflow_id)]

        # Create a column for the stimuli to append to the EEG data
        stim_array = create_stim_array(timestamps, self.markers)
        timestamps = timestamps[
            ..., None
        ]  # Add an additional dimension so that shapes match
        total_data = np.append(timestamps, eeg_data, 1)
        total_data = np.append(
            total_data, stim_array, 1
        )  # Append the stim array to data.

        # Subtract five seconds of settling time from beginning
        # total_data = total_data[5 * self.sfreq :]
        df = pd.DataFrame(total_data, columns=["timestamps"] + ch_names + ["stim"])
        return df

    def _save(self) -> None:
        """Saves the data to a CSV file."""
        assert self.save_fn
        df = self.get_data()
        df.to_csv(self.save_fn, index=False)

    def _stop_brainflow(self) -> None:
        """This functions kills the brainflow backend and saves the data to a CSV file."""
        # Collect session data and kill session
        if self.save_fn:
            self._save()
        self.board.stop_stream()
        self.board.release_session()


def test_check():
    device = BrainflowDevice(device_name="synthetic")
    with device:
        sleep(2)  # is 2s really needed?
        bads = device.check(max_uv_abs=300)
        # Seems to blink between the two...
        assert bads == ["F6", "F8"] or bads == ["F4", "F6", "F8"]
        # print(bads)
        # assert not bads


def test_get_data():
    device = BrainflowDevice(device_name="synthetic")
    with device:
        sleep(2)
        df = device.get_data()
        print(df)
        assert not df.empty
