from eegnb import DATA_DIR
import click
from time import sleep
from os import path
import os
import shutil
from eegnb.datasets.datasets import zip_data_folders

from .introprompt import intro_prompt, analysis_intro_prompt
from .utils import run_experiment
from eegnb import generate_save_fn
from eegnb.devices.eeg import EEG
from eegnb.analysis.utils import check_report
from eegnb.analysis.pipelines import load_eeg_data, make_erp_plot, create_analysis_report


@click.group(name="eegnb")
def main():
    """eeg-notebooks command line interface"""
    pass


@main.command()
@click.option("-ex", "--experiment", help="Experiment to run")
@click.option("-ed", "--eegdevice", help="EEG device to use")
@click.option("-ma", "--macaddr", help="MAC address of device to use (if applicable)")
@click.option("-rd", "--recdur", help="Recording duration", type=float)
@click.option("-of", "--outfname", help="Output filename")
@click.option(
    "-ip", "--prompt", help="Use interactive prompt to ask for parameters", is_flag=True
)
def runexp(
    experiment: str,
    eegdevice: str = None,
    macaddr: str = None,
    recdur: float = None,
    outfname: str = None,
    prompt: bool = False,
    dosigqualcheck = True,
    generatereport = True
):
    """
    Run experiment.

    Examples:

    Run experiment explicitly defining all necessary parameters
    (eeg device, experiment, duration, output file)
    This is the quickest way to run eeg-notebooks experiments,
    but requires knowledge of formatting for available options

    $ eegnb runexp -ex visual-N170 -ed museS -rd 10 -of test.csv


    Launch the interactive command line experiment setup+run tool
    This takes you through every experiment parameter in order
    and figures out + runs the complete function calls for you

    $ eegnb runexp -ip
    """

    if prompt:
        eeg, experiment, recdur, outfname = intro_prompt()
    else:
        # Random values for outfile for now
        outfname = generate_save_fn(eegdevice, experiment,7, 7)
        if eegdevice == "ganglion":
            # if the ganglion is chosen a MAC address should also be provided
            eeg = EEG(device=eegdevice, mac_addr=macaddr)
        else:
            eeg = EEG(device=eegdevice)

    def askforsigqualcheck():
        do_sigqual = input("\n\nRun signal quality check? (y/n). Recommend y \n")
        if do_sigqual == 'y':
            check_report(eeg)
        elif do_sigqual != 'n':
            "Sorry, didn't recognize answer. "
            askforsigqualcheck()
    
    def askforreportcheck():
        do_sigqual = input("\n\nGenerate Report? (y/n). Recommend y \n")
        if do_sigqual != 'y':
            generatereport= False

    if dosigqualcheck:
        askforsigqualcheck()
    
    if generatereport:
        askforreportcheck()

    run_experiment(experiment, eeg, recdur, outfname)

    print(f"\n\n\nExperiment complete! Recorded data is saved @ {outfname}")

    if generatereport:
        create_analysis_report(experiment, eegdevice, outfname)


@main.command()
@click.option("-ex", "--experiment", help="Experiment to run")
@click.option("-ed", "--eegdevice", help="EEG device to use")
@click.option("-sub", "--subject", help="Subject ID")
@click.option("-sess", "--session", help="Session number")
@click.option(
    "-ip", "--prompt", help="Use interactive prompt to ask for parameters", is_flag=True
)
def create_analysis_report(
    experiment: str,
    eegdevice: str = None,
    subject: str = None, 
    session: str = None,
    prompt: bool = False,
    filepath:str = None
):
    """
    Create analysis report of recorded data
    """
    if prompt:
        eegdevice, experiment, subject, session, filepath = analysis_intro_prompt()
    create_analysis_report(experiment, eegdevice, subject, session, filepath)
    return

@main.command()
@click.option("-ed", "--eegdevice", help="EEG device to use", required=True)
def checksigqual(eegdevice: str):
    """
    Run signal quality check.

    Usage:
        eegnb checksigqual --eegdevice museS
    """

    from eegnb.devices.eeg import EEG
    from eegnb.analysis.utils import check_report

    eeg = EEG(device=eegdevice)

    check_report(eeg)

    # TODO: implement command line options for non-default check_report params
    #       ( n_times, pause_time, thres_var, etc. )
    #       [ tried to do this but keeps defaulting to None rather than default
    #         valuess in the function definition ]




@main.command()
@click.option("-ex", "--experiment", help="Experiment to zip", required=False)
@click.option(
    "-s", "--site", help="Specific Directory", default="local_ntcs", required=False
)
@click.option(
    "-ip", "--prompt", help="Use interactive prompt to ask for parameters", is_flag=True
)
def runzip(experiment: str, site: str, prompt: bool = False):

    """eeg
    Run data zipping

    Usage

    $ eegnb runzip -ex visual-N170
    $ eegnb runzip -ex visual-N170 -s local-ntcs-2
    
    Launch the interactive command line to select experiment

    $ eegnb runzip -ip

    """

    if prompt:
        from .introprompt import intro_prompt_zip

        experiment, site = intro_prompt_zip()

    zip_data_folders(experiment, site)


@main.command()
def localdata_report():
    """
    Run local data summary

    Usage

    $eegnb localdata-report
    """

    print("\n EEG-Notebooks Local Data Report")
    print("\n ===============================\n")
    print(
        " Here is a short report of eeg-notebooks-related EEG data that was found on this machine:\n"
    )

    directory_contents = os.listdir(DATA_DIR)
    # print(directory_contents)

    example_datasets = []
    recorded_datasets = []
    for dir in directory_contents:

        dir_contents = os.path.join(DATA_DIR, dir)
        subdir_contents = os.listdir(dir_contents)
        for subdir in subdir_contents:
            subdir_path = os.path.join(DATA_DIR, dir, subdir)
            print(subdir_path)
            if os.path.isdir(subdir_path):
                if len(os.listdir(subdir_path)) == 0:
                    subdir_path = subdir_path + " [EMPTY]"
                if "eegnb_examples" in subdir:
                    example_datasets.append(subdir_path)
                else:
                    recorded_datasets.append(subdir_path)

    print("\n 1. Default Data \n")
    print(" ------------------\n")
    print(" The default eeg-notebooks data location on this machine is\n")
    print(" {}".format(DATA_DIR))
    print("\n (note that `.eegnb` is a hidden folder)\n")
    print("\n Folders where you have downloaded the eeg-notebooks example datasets:\n")
    for items in example_datasets:
        print(" {}".format(items))

    print("\n\n 2. Your recorded data\n")
    print(" ------------------\n")
    print("\n Folders where you have recorded your own data:\n")
    for items in recorded_datasets:
        print(" {}".format(items))


if __name__ == "__main__":
    main()
