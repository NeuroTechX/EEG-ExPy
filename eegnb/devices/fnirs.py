""" Abstraction for the various supported fNIRS devices.

    1. Determine which backend to use for the board.
    2.

"""

import sys
#import datetime,time
import logging
from datetime import datetime
from time import time, sleep
from multiprocessing import Process

import numpy as np
import pandas as pd

from brainflow import BoardShim, BoardIds, BrainFlowInputParams
from muselsl import stream, list_muses, record, constants as mlsl_cnsts
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_byprop

from eegnb.devices.utils import get_openbci_usb, create_stim_array,SAMPLE_FREQS,EEG_INDICES,EEG_CHANNELS

import socket
import json

import h5py

logger = logging.getLogger(__name__)




# list of fnirs devices
kernel_devices = ["kernelflow"]


class FNIRS:
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
    ):
        """The initialization function...

        Parameters:
            device (str): name of fnirs device used for reading data.
        """

        # determine if board uses brainflow or muselsl backend
        self.device_name = device
        self.serial_num = serial_num
        self.serial_port = serial_port
        self.mac_address = mac_addr
        self.ip_addr = ip_addr
        self.other = other
        self.backend = self._get_backend(self.device_name)
        self.initialize_backend()
        #self.n_channels = len(EEG_INDICES[self.device_name])
        #self.sfreq = SAMPLE_FREQS[self.device_name]
        #self.channels = EEG_CHANNELS[self.device_name]
        self.kernel = None

        self.kernel_logfile_fname = ''
        self.kernel_logfile_txt = ''
        self.kernel_evlen = None



    def initialize_backend(self):
        if self.backend == "kernel":
            self._init_kernel()
            #self.timestamp_channel = BoardShim.get_timestamp_channel(self.brainflow_id)
        #elif self.backend == "muselsl":
        #    self._init_muselsl()
        #    self._muse_get_recent() # run this at initialization to get some 
        #                            # stream metadata into the eeg class

    def _get_backend(self, device_name):
        if device_name in kernel_devices:
            return "kernel"
        #elif device_name in ["muse2016", "muse2", "museS"]:
        #    return "muselsl"

    #####################
    #  KERNEL Functions #
    #####################

    def _init_kernel(self):
        # Currently there's nothing we need to do here. However keeping the
        # option open to add things with this init method.
        self._notes = None #muse_recent_inlet = None

    def _start_kernel(self): #:, duration):

        start_timestamp = int(time()*1e9)
        
        # Create log file
        dtstr = str(datetime.now()).replace(' ', '_').split('.')[0]
        self.kernel_logfile_fname = '/tmp/eegnb_kf_logfile__%s.txt' % dtstr
        self.kernel_logfile_txt = []

        # Send first data packet 
        data_to_send = {"id": 0,
                        "timestamp": start_timestamp,
                        "event": "start_experiment",
                        "value": "0"
                        }
        kernel_sendpack(data_to_send)
        
        # Update logfile text
        self.kernel_evlen=0
        self.kernel_logfile_txt.append(data_to_send)


    def _kernel_push_sample(self, timestamp, marker, marker_name):

        # Send trigger
        adj_timestamp = int(timestamp*1e9)
        data_to_send = {
                         "id": marker, #event_id,
                         "timestamp": adj_timestamp,
                         "event": marker_name, #event_name,
                         "value":"1",
                        }
        kernel_sendpack(data_to_send)

        # Update logfile text
        self.kernel_evlen+=1            
        self.kernel_logfile_txt.append(data_to_send)


    def _stop_kernel(self):


        stop_timestamp = int(time()*1e9)
        
        data_to_send = {
                        "id": self.kernel_evlen+1,
                        "timestamp": stop_timestamp,
                         "event": "end_experiment",
                         "value": "2",
                        }
        kernel_sendpack(data_to_send)

        self.kernel_logfile_txt.append(data_to_send)


        print('writing kf eegnb logfile to %s' %self.kernel_logfile_fname)
        F = open(self.kernel_logfile_fname, 'w+')
        json.dump(self.kernel_logfile_txt,F)
        F.close()
   

    #################################
    #   Highlevel device functions  #
    #################################

    def start(self,fn=None): #, duration=None):
        """Starts the FNIRS device based on the defined backend.

        Parameters:
            fn (str): name of the file to save the sessions data to.
        """
        if fn:
            self.save_fn = fn

        if self.backend == "kernel":
            self._start_kernel()
            #self.markers = []

    def push_sample(self, timestamp, marker, marker_name = None):
        """
        Universal method for pushing a marker and its timestamp to store alongside the fNIRS data.

        Parameters:
            marker (int): marker number for the stimuli being presented.
            marker (str): optional marker name
            timestamp (float): timestamp of stimulus onset from time.time() function.
        """
        if self.backend == "kernel":
            self._kernel_push_sample(timestamp=timestamp,marker=marker,marker_name=marker_name)

    def stop(self):
        if self.backend == "kernel":
            self._stop_kernel()



def kernel_sendpack(data_to_send):
    event_to_send = json.dumps(data_to_send).encode("utf-8")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(event_to_send, ("239.128.35.86", 7891))
    
