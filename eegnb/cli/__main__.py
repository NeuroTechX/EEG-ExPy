import click
from time import sleep


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
        # import and run the introprompt script
        from .introprompt import main as run_introprompt

        run_introprompt()
    else:
        from .utils import run_experiment
        from eegnb.devices.eeg import EEG

        if eegdevice == "ganglion":
            # if the ganglion is chosen a MAC address should also be proviced
            eeg = EEG(device=eegdevice, mac_addr=macaddr)
        else:
            eeg = EEG(device=eegdevice)

        run_experiment(experiment, eeg, recdur, outfname)



@main.command()
@click.option("-ed", "--eegdevice", help="EEG device to use", required=True)
def checkreport(eegdevice: str):
    """
    Run signal quality check.

    Usage:
        eegnb checkreport --eegdevice museS
    """
    
    from eegnb.devices.eeg import EEG
    from eegnb.analysis.utils import check_report 
    eeg = EEG(device=eegdevice)
    
    check_report(eeg)
    
    # TODO: implement command line options for non-default check_report params
    #       ( n_times, pause_time, thres_var, etc. )
    #       [ tried to do this but keeps defaulting to None rather than default 
    #         valuess in the function definition ]
    
    

if __name__ == "__main__":
    main()
