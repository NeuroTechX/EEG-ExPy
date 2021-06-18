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
def check(eegdevice: str, n_times=5, pause_time=5, thres_var=100):
    """
    Run signal quality check.

    Usage:
        eegnb check --eegdevice museS
    """
    print("Running signal quality check...")
    print(f"Using threshold variance: {thres_var}")
    from eegnb.devices.eeg import EEG

    CHECKMARK = "✓"
    CROSS = "x"

    eeg = EEG(device=eegdevice)
    # eeg.start(None)

    for _ in range(n_times):
        res, var = eeg.check(n_samples=pause_time * 256)

        indicators = "\n".join(
            [
                f"  {k:>4}: {CHECKMARK if v else CROSS}   (var: {round(var[k], 1):>5})"
                for k, v in res.items()
            ]
        )
        print("\nSignal quality:")
        print(indicators)

        bad_channels = [k for k, v in res.items() if not v]
        if bad_channels:
            print(f"Bad channels: {', '.join(bad_channels)}")
        else:
            print("All good!")
            # TODO: Check that signal stays good for a while?
            break

        sleep(pause_time)


if __name__ == "__main__":
    main()
