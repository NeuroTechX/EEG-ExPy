""" Abstraction for the various supported EEG devices.

    1. Determine which backend to use for the board.
    2.

"""

import sys
import time
import logging
from time import sleep
from multiprocessing import Process

import numpy as np
import pandas as pd

from brainflow.board_shim import BoardShim, BoardIds, BrainFlowInputParams
from muselsl import stream, list_muses, record, constants as mlsl_cnsts
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_byprop

from eegnb.devices.utils import (
    get_openbci_usb,
    create_stim_array,
    SAMPLE_FREQS,
    EEG_INDICES,
    EEG_CHANNELS,
)


logger = logging.getLogger(__name__)

# list of brainflow devices
brainflow_devices = [
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
    "freeeeg32",
    "crown",
    "museS_bfn",  # bfn = brainflow with native bluetooth;
    "museS_bfb",  # bfb = brainflow with BLED dongle bluetooth
    "muse2_bfn",
    "muse2_bfb",
    "muse2016_bfn",
    "muse2016_bfb",
]


class EEG:
    device_name: str
    stream_started: bool = False

    def __init__(
        self,
        device=None,
        serial_port=None,
        serial_num=None,
        mac_addr=None,
        other=None,
        ip_addr=None,
        ch_names=None,
        config=None
    ):
        """The initialization function takes the name of the EEG device and determines whether or not
        the device belongs to the Muse or Brainflow families and initializes the appropriate backend.

        Parameters:
            device (str): name of eeg device used for reading data.
        
            ch_names (array_like or None): array containing custom specified channel names. Useful for custom montagues 
        like when external electrodes are used.
        """
        # determine if board uses brainflow or muselsl backend
        self.device_name = device
        self.serial_num = serial_num
        self.serial_port = serial_port
        self.mac_address = mac_addr
        self.ip_addr = ip_addr
        self.other = other
        self.config = config
        self.backend = self._get_backend(self.device_name)
        self.initialize_backend()
        self.n_channels = len(EEG_INDICES[self.device_name])
        self.sfreq = SAMPLE_FREQS[self.device_name]
        self.channels = EEG_CHANNELS[self.device_name]
        self.ch_names = ch_names

    def initialize_backend(self):
        if self.backend == "brainflow":
            self._init_brainflow()
            self.timestamp_channel = BoardShim.get_timestamp_channel(self.brainflow_id)
        elif self.backend == "muselsl":
            self._init_muselsl()
            self._muse_get_recent()  # run this at initialization to get some
            # stream metadata into the eeg class

    def _get_backend(self, device_name):
        if device_name in brainflow_devices:
            return "brainflow"
        elif device_name in ["muse2016", "muse2", "museS"]:
            return "muselsl"

    #####################
    #   MUSE functions  #
    #####################
    def _init_muselsl(self):
        # Currently there's nothing we need to do here. However keeping the
        # option open to add things with this init method.
        self._muse_recent_inlet = None

    def _start_muse(self, duration):
        if sys.platform in ["linux", "linux2", "darwin"]:
            # Look for muses
            self.muses = list_muses()
            # self.muse = muses[0]

            # Start streaming process
            self.stream_process = Process(
                target=stream, args=(self.muses[0]["address"],)
            )
            self.stream_process.start()

        # Create markers stream outlet
        self.muse_StreamInfo = StreamInfo(
            "Markers", "Markers", 1, 0, "int32", "myuidw43536"
        )
        self.muse_StreamOutlet = StreamOutlet(self.muse_StreamInfo)

        # Start a background process that will stream data from the first available Muse
        print("starting background recording process")
        if self.save_fn:
            print("will save to file: %s" % self.save_fn)
        self.recording = Process(target=record, args=(duration, self.save_fn))
        self.recording.start()

        time.sleep(5)
        self.stream_started = True
        self.push_sample([99], timestamp=time.time())

    def _stop_muse(self):
        pass

    def _muse_push_sample(self, marker, timestamp):
        self.muse_StreamOutlet.push_sample(marker, timestamp)

    def _muse_get_recent(self, n_samples: int = 256, restart_inlet: bool = False):
        if self._muse_recent_inlet and not restart_inlet:
            inlet = self._muse_recent_inlet
        else:
            # Initiate a new lsl stream
            streams = resolve_byprop("type", "EEG", timeout=mlsl_cnsts.LSL_SCAN_TIMEOUT)
            if not streams:
                raise Exception("Couldn't find any stream, is your device connected?")
            inlet = StreamInlet(streams[0], max_chunklen=mlsl_cnsts.LSL_EEG_CHUNK)
            self._muse_recent_inlet = inlet

        info = inlet.info()
        sfreq = info.nominal_srate()
        description = info.desc()
        n_chans = info.channel_count()

        self.sfreq = sfreq
        self.info = info
        self.n_chans = n_chans

        timeout = (n_samples / sfreq) + 0.5
        samples, timestamps = inlet.pull_chunk(timeout=timeout, max_samples=n_samples)

        samples = np.array(samples)
        timestamps = np.array(timestamps)

        ch = description.child("channels").first_child()
        ch_names = [ch.child_value("label")]
        for i in range(n_chans):
            ch = ch.next_sibling()
            lab = ch.child_value("label")
            if lab != "":
                ch_names.append(lab)

        df = pd.DataFrame(samples, index=timestamps, columns=ch_names)
        return df

    ##########################
    #   BrainFlow functions  #
    ##########################
    def _init_brainflow(self):
        """This function initializes the brainflow backend based on the input device name. It calls
        a utility function to determine the appropriate USB port to use based on the current operating system.
        Additionally, the system allows for passing a serial number in the case that they want to use either
        the BraintBit or the Unicorn EEG devices from the brainflow family.

        Parameters:
             serial_num (str or int): serial number for either the BrainBit or Unicorn devices.
        """
        # Initialize brainflow parameters
        self.brainflow_params = BrainFlowInputParams()

        if self.device_name == "ganglion":
            self.brainflow_id = BoardIds.GANGLION_BOARD.value
            if self.serial_port is None:
                self.brainflow_params.serial_port = get_openbci_usb()
            # set mac address parameter in case
            if self.mac_address is None:
                print("No MAC address provided, attempting to connect without one")
            else:
                self.brainflow_params.mac_address = self.mac_address

        elif self.device_name == "ganglion_wifi":
            self.brainflow_id = BoardIds.GANGLION_WIFI_BOARD.value
            if self.ip_addr is not None:
                self.brainflow_params.ip_address = self.ip_addr
                self.brainflow_params.ip_port = 6677

        elif self.device_name == "cyton":
            self.brainflow_id = BoardIds.CYTON_BOARD.value
            if self.serial_port is None:
                self.brainflow_params.serial_port = get_openbci_usb()

        elif self.device_name == "cyton_wifi":
            self.brainflow_id = BoardIds.CYTON_WIFI_BOARD.value
            if self.ip_addr is not None:
                self.brainflow_params.ip_address = self.ip_addr
                self.brainflow_params.ip_port = 6677

        elif self.device_name == "cyton_daisy":
            self.brainflow_id = BoardIds.CYTON_DAISY_BOARD.value
            if self.serial_port is None:
                self.brainflow_params.serial_port = get_openbci_usb()

        elif self.device_name == "cyton_daisy_wifi":
            self.brainflow_id = BoardIds.CYTON_DAISY_WIFI_BOARD.value
            if self.ip_addr is not None:
                self.brainflow_params.ip_address = self.ip_addr

        elif self.device_name == "brainbit":
            self.brainflow_id = BoardIds.BRAINBIT_BOARD.value

        elif self.device_name == "unicorn":
            self.brainflow_id = BoardIds.UNICORN_BOARD.value

        elif self.device_name == "callibri_eeg":
            self.brainflow_id = BoardIds.CALLIBRI_EEG_BOARD.value
            if self.other:
                self.brainflow_params.other_info = str(self.other)

        elif self.device_name == "notion1":
            self.brainflow_id = BoardIds.NOTION_1_BOARD.value

        elif self.device_name == "notion2":
            self.brainflow_id = BoardIds.NOTION_2_BOARD.value

        elif self.device_name == "crown":
            self.brainflow_id = BoardIds.CROWN_BOARD.value

        elif self.device_name == "freeeeg32":
            self.brainflow_id = BoardIds.FREEEEG32_BOARD.value
            if self.serial_port is None:
                self.brainflow_params.serial_port = get_openbci_usb()

        elif self.device_name == "museS_bfn":
            self.brainflow_id = BoardIds.MUSE_S_BOARD.value

        elif self.device_name == "museS_bfb":
            self.brainflow_id = BoardIds.MUSE_S_BLED_BOARD.value

        elif self.device_name == "muse2_bfn":
            self.brainflow_id = BoardIds.MUSE_2_BOARD.value

        elif self.device_name == "muse2_bfb":
            self.brainflow_id = BoardIds.MUSE_2_BLED_BOARD.value

        elif self.device_name == "muse2016_bfn":
            self.brainflow_id = BoardIds.MUSE_2016_BOARD.value

        elif self.device_name == "muse2016_bfb":
            self.brainflow_id = BoardIds.MUSE_2016_BLED_BOARD.value

        elif self.device_name == "synthetic":
            self.brainflow_id = BoardIds.SYNTHETIC_BOARD.value

        # some devices allow for an optional serial number parameter for better connection
        if self.serial_num:
            serial_num = str(self.serial_num)
            self.brainflow_params.serial_number = serial_num

        if self.serial_port:
            serial_port = str(self.serial_port)
            self.brainflow_params.serial_port = serial_port

        # Initialize board_shim
        self.sfreq = BoardShim.get_sampling_rate(self.brainflow_id)
        self.board = BoardShim(self.brainflow_id, self.brainflow_params)
        self.board.prepare_session()

        # Apply board configuration if provided
        if self.config:
            # For Cyton boards, split config string by 'X' delimiter and apply each setting
            if 'cyton' in self.device_name:
                config_settings = self.config.split('X')
                for setting in config_settings:
                    self.board.config_board(setting + 'X')
            else:
                self.board.config_board(self.config)

    def _start_brainflow(self):
        # only start stream if non exists
        if not self.stream_started:
            self.board.start_stream()

        self.stream_started = True

        # wait for signal to settle
        if (self.device_name.find("cyton") != -1) or (
            self.device_name.find("ganglion") != -1
        ):
            # wait longer for openbci cyton / ganglion
            sleep(10)
        else:
            sleep(5)

    def _stop_brainflow(self):
        """This functions kills the brainflow backend and saves the data to a CSV file."""

        # Collect session data and kill session
        data = self.board.get_board_data()  # will clear board buffer
        self.board.stop_stream()
        self.board.release_session()

        # Extract relevant metadata from board
        ch_names, eeg_data, timestamps = self._brainflow_extract(data)

        # Create a column for the stimuli to append to the EEG data
        stim_array = create_stim_array(timestamps, self.markers)
        timestamps = timestamps[..., None]

        # Add an additional dimension so that shapes match
        total_data = np.append(timestamps, eeg_data, 1)

        # Append the stim array to data.
        total_data = np.append(total_data, stim_array, 1)

        # Subtract five seconds of settling time from beginning
        total_data = total_data[5 * self.sfreq :]
        data_df = pd.DataFrame(total_data, columns=["timestamps"] + ch_names + ["stim"])
        data_df.to_csv(self.save_fn, index=False)

    def _brainflow_extract(self, data):
        """
        Formats the data returned from brainflow to get
        ch_names; list of channel names
        eeg_data: NDArray of eeg samples
        timestamps: NDArray of timestamps
        """

        # transform data for saving
        data = data.T  # transpose data

        # explicitly assign channel names for EEG data
        if self.ch_names is not None:
            ch_names = self.ch_names
        # automatically assign the channel names for EEG data
        elif (
            self.brainflow_id == BoardIds.GANGLION_BOARD.value
            or self.brainflow_id == BoardIds.GANGLION_WIFI_BOARD.value
        ):
            # if a ganglion is used, use recommended default EEG channel names
            ch_names = ["fp1", "fp2", "tp7", "tp8"]
        elif self.brainflow_id == BoardIds.FREEEEG32_BOARD.value:
            ch_names = [f"eeg_{i}" for i in range(0, 32)]
        else:
            # otherwise select eeg channel names via brainflow API
            ch_names = BoardShim.get_eeg_names(self.brainflow_id)

        # pull EEG channel data via brainflow API
        eeg_data = data[:, BoardShim.get_eeg_channels(self.brainflow_id)]
        timestamps = data[:, BoardShim.get_timestamp_channel(self.brainflow_id)]

        return ch_names, eeg_data, timestamps

    def _brainflow_push_sample(self, marker):
        last_timestamp = self.board.get_current_board_data(1)[self.timestamp_channel][0]
        self.markers.append([marker, last_timestamp])

    def _brainflow_get_recent(self, n_samples=256):

        # initialize brainflow if not set
        if self.board == None:
            self._init_brainflow()

        # start branflow stream
        self._start_brainflow()

        # get the latest data
        data = self.board.get_current_board_data(n_samples)

        ch_names, eeg_data, timestamps = self._brainflow_extract(data)

        eeg_data = np.array(eeg_data)
        timestamps = np.array(timestamps)

        df = pd.DataFrame(eeg_data, index=timestamps, columns=ch_names)
        # print (df)
        return df

    #################################
    #   Highlevel device functions  #
    #################################

    def start(self, fn, duration=None):
        """Starts the EEG device based on the defined backend.

        Parameters:
            fn (str): name of the file to save the sessions data to.
        """
        if fn:
            self.save_fn = fn

        if self.backend == "brainflow":
            self._start_brainflow()
            self.markers = []
        elif self.backend == "muselsl":
            self._start_muse(duration)

    def push_sample(self, marker, timestamp):
        """
        Universal method for pushing a marker and its timestamp to store alongside the EEG data.

        Parameters:
            marker (int): marker number for the stimuli being presented.
            timestamp (float): timestamp of stimulus onset from time.time() function.
        """
        if self.backend == "brainflow":
            self._brainflow_push_sample(marker=marker)
        elif self.backend == "muselsl":
            self._muse_push_sample(marker=marker, timestamp=timestamp)

    def stop(self):
        if self.backend == "brainflow":
            self._stop_brainflow()
        elif self.backend == "muselsl":
            pass

    def get_recent(self, n_samples: int = 256):
        """
        Usage:
        -------
        from eegnb.devices.eeg import EEG
        this_eeg = EEG(device='museS')
        df_rec = this_eeg.get_recent()
        """

        if self.backend == "brainflow":
            df = self._brainflow_get_recent(n_samples)
        elif self.backend == "muselsl":
            df = self._muse_get_recent(n_samples)
        else:
            raise ValueError(f"Unknown backend {self.backend}")

        # Sort out the sensor coils
        sorted_cols = sorted(df.columns)
        df = df[sorted_cols]

        return df
