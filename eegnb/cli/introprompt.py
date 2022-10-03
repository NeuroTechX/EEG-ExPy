import os 
from typing import Tuple
from pathlib import Path

from eegnb import generate_save_fn, DATA_DIR
from eegnb.devices.eeg import EEG
from .utils import run_experiment, get_exp_desc, experiments

eegnb_sites = ['eegnb_examples', 'grifflab_dev', 'jadinlab_home']

def device_prompt() -> EEG: 
    # define the names of the available boards
    # boards is a mapping from board code to board description
    boards = {
        "none": "None",
        "muse2016": "Muse (2016)",
        "muse2": "Muse 2",
        "museS": "Muse S",
        "muse2016_bfn": "Muse 2016 - brainflow, native bluetooth",
        "muse2016_bfb": "Muse 2016 - brainflow, BLED bluetooth dongle",        
        "muse2_bfn": "Muse 2 - brainflow, native bluetooth",
        "muse2_bfb": "Muse 2 - brainflow, BLED bluetooth dongle",
        "museS_bfn": "Muse S - brainflow, native bluetooth",
        "museS_bfb": "Muse S - brainflow, BLED bluetooth dongle",
        "ganglion": "OpenBCI Ganglion",
        "cyton": "OpenBCI Cyton",
        "cyton_daisy": "OpenBCI Cyton + Daisy",
        "unicorn": "G.Tec Unicorn",
        "brainbit": "BrainBit",
        "notion1": "Notion 1",
        "notion2": "Notion 2",
        "crown": "Crown",
        "synthetic": "Synthetic",
        "freeeeg32": "FreeEEG32",
    }

    print("Please enter the integer value corresponding to your EEG device: \n")
    print("\n".join(f"[{i:2}] {board}" for i, board in enumerate(boards.values())))

    board_idx = int(input("\nEnter Board Selection: "))

    # Board_codes are the actual names to be passed to the EEG class
    board_code = list(boards.keys())[board_idx]
    board_desc = list(boards.values())[board_idx]

    print(f"Selected board: {board_desc} \n")

    # Handles connectivity selection if an OpenBCI board is being used
    if board_code in ["cyton", "cyton_daisy", "ganglion"]:

        # determine whether board is connected via Wifi or BLE
        print(
            "Please select your connection method:\n"
            "[0] usb dongle \n"
            "[1] wifi shield \n"
        )
        connect_idx = int(input("Enter connection method: "))

        # add "_wifi" suffix to the end of the board name for brainflow
        if connect_idx == 1:
            board_code = board_code + "_wifi"
        if board_code == "ganglion":
            # If the Ganglion is being used, you can enter optional Ganglion mac address
            ganglion_mac_address = input(
                "\nGanglion MAC Address (Press Enter to Autoscan): "
            )
        elif board_code == "ganglion_wifi":
            # IP address is required for this board configuration
            ip_address = input("\nEnter Ganglion+WiFi IP Address: ")
        elif board_code == "cyton_wifi" or board_code == "cyton_daisy_wifi":
            print(
                f"\n{board_desc} + WiFi is not supported. Please use the dongle that was shipped with the device.\n"
            )
            exit()
       
    if board_code.startswith("ganglion"):
        if board_code == "ganglion_wifi":
            eeg_device = EEG(device=board_code, ip_addr=ip_address)
        else:
            eeg_device = EEG(device=board_code, mac_addr=ganglion_mac_address)
    else:
        eeg_device = EEG(device=board_code)

    return eeg_device



def exp_prompt(runorzip:str='run') -> str:
    print("\nPlease select which experiment you would like to %s: \n" %runorzip)
    print(
        "\n".join(
            [
                "[{}] {}".format(i, get_exp_desc(exp))
                for i, exp in enumerate(experiments.keys())
            ]
        )
    )

    exp_idx = int(input("\nEnter Experiment Selection: "))
    exp_selection = list(experiments.keys())[exp_idx]
    print(f"Selected experiment: {exp_selection} \n")

    return exp_selection

def site_prompt(experiment:str) -> str:
    experiment_dir=os.path.join(DATA_DIR,experiment)
        
    if not (os.path.isdir(experiment_dir)):
        print('Folder {} does not exist in {}\n'.format(experiment,DATA_DIR))
        raise ValueError ('Directory does not exist')

    if len(os.listdir(experiment_dir) ) == 0:
        print('No subfolders exist in {}' .format(experiment_dir))
        raise ValueError ('Directory is empty')  

    print("\nPlease select which experiment subfolder you would like to zip. Default 'local_ntcs'")
    print("\nCurrent subfolders for experiment {}:\n".format(experiment))
    dirslist = [d for d in os.listdir(experiment_dir) if d not in eegnb_sites ]
    for d in dirslist: print(d + '\n')
    site=str(input('\nType folder name: '))
    if site=="":
        site="local"

    print("Selected Folder : {} \n".format(site))
    return site

def intro_prompt() -> Tuple[EEG, str, int, str]:
    """This function handles the user prompts for inputting information about the session they wish to record."""
    print("Welcome to NeurotechX EEG Notebooks\n")

    # ask the user which device to use
    eeg_device = device_prompt()

    # ask the user which experiment to run
    exp_selection = exp_prompt()

    # record duration
    print("Now, enter the duration of the recording (in seconds). \n")
    duration = int(input("Enter duration: "))

    # Subject ID specification
    print("\nNext, enter the ID# of the subject you are recording data from. \n")
    subj_id = int(input("Enter subject ID#: "))

    # Session ID specification
    print("\nNext, enter the session number you are recording for. \n")
    session_nb = int(input("Enter session #: "))

    # ask if they are ready to begin
    #print("\nEEG device successfully connected!")
    #input("Press [ENTER] when ready to begin...")

    # generate the save file name
    save_fn = generate_save_fn(
        eeg_device.device_name, exp_selection, subj_id, session_nb 
    )

    return eeg_device, exp_selection, duration, str(save_fn)


def intro_prompt_zip() -> Tuple[str,str]:
    """This function handles the user prompts for inputting information for zipping their function."""

    # ask the user which experiment to zip
    exp_selection = exp_prompt(runorzip='zip')
    site= site_prompt(exp_selection)
    
    return exp_selection,site


def main() -> None:
    eeg_device, experiment, record_duration, save_fn = intro_prompt()
    run_experiment(experiment, eeg_device, record_duration, save_fn)


if __name__ == "__main__":
    main()
