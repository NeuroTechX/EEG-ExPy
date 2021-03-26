#!/usr/bin/python
import sys
import argparse


class CLI:
    def __init__(self, command):
        # use dispatch pattern to invoke method with same name
        getattr(self, command)()

    def runexp(self):

        parser = argparse.ArgumentParser(description="Run EEG experiment.")

        parser.add_argument(
            "-ed",
            "--eegdevice",
            dest="eeg_device",
            type=str,
            default=None,
            help="add help here",
        )

        parser.add_argument(
            "-ma",
            "--macaddr",
            dest="mac_address",
            type=str,
            default=False,
            help="add help here",
        )

        parser.add_argument(
            "-ex",
            "--expt",
            dest="experiment",
            type=str,
            default=None,
            help="add help str",
        )

        parser.add_argument(
            "-rd",
            "--recdur",
            dest="record_duration",
            type=str,
            default=None,
            help="add help str",
        )

        parser.add_argument(
            "-of",
            "--outfname",
            dest="save_fn",
            type=str,
            default=None,
            help="add help str",
        )

        parser.add_argument(
            "-ip", "--inprom", dest="inprompt", action="store_true", help="add help str"
        )

        args = parser.parse_args(sys.argv[2:])

        if args.inprompt:
            print("run command line prompt script")
            from .introprompt import main as run_introprompt

            run_introprompt()
        else:
            from .utils import run_experiment
            from eegnb.devices.eeg import EEG

            if args.eeg_device == "ganglion":
                # if the ganglion is chosen a MAC address should also be proviced
                eeg_device = EEG(device=args.eeg_device, mac_addr=args.mac_address)
            else:
                eeg_device = EEG(device=args.eeg_device)

            run_experiment(
                args.experiment, args.record_duration, eeg_device, args.save_fn
            )

    def view(self):
        print("add viewer functionality here")

        # args = parser.parse_args(sys.argv[2:])
        # from . import view
        # view(args.window, args.scale, args.refresh,
        #     args.figure, args.version, args.backend)
