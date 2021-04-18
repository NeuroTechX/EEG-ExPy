import click
import logging

logger = logging.getLogger(__name__)


@click.group(name="eegnb")
def main():
    """eeg-notebooks command line interface"""
    logging.basicConfig(level=logging.INFO)


@main.command()
@click.option(
    "-ex",
    "--experiment",
    help="Experiment to run",
    prompt="Experiment to run",
)
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

    $ eegnb runexp -ed museS -ex visual-N170 -rd 10 -of test.csv


    Launch the interactive command line experiment setup+run tool
    This takes you through every experiment parameter in order
    and figures out + runs the complete function calls for you

    $ eegnb runexp -ip
    """
    if prompt:
        print("run command line prompt script")
        from .introprompt import main as run_introprompt

        run_introprompt()
    else:
        from .utils import run_experiment
        from eegnb.devices import EEGDevice

        if eegdevice == "ganglion":
            # if the ganglion is chosen a MAC address should also be proviced
            eeg = EEGDevice.create(device_name=eegdevice, mac_addr=macaddr)
        else:
            if eegdevice:
                eeg = EEGDevice.create(device_name=eegdevice)
            else:
                print("No EEG device provided, using a synthetic one.")

        run_experiment(experiment, eeg, recdur, outfname)


@main.command()
@click.option("-ed", "--eegdevice", help="EEG device to use")
@click.option("-vr", "--version", help="Viewer version (for muselsl)")
def view():
    """
    View live EEG stream.

    Examples: TODO
    """
    print("add viewer functionality here")

    # args = parser.parse_args(sys.argv[2:])
    # from . import view
    # view(args.window, args.scale, args.refresh,
    #     args.figure, args.version, args.backend)

    raise NotImplementedError


def test_cli():
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0

    runner = CliRunner()
    result = runner.invoke(runexp, ["--help"])
    assert result.exit_code == 0


if __name__ == "__main__":
    main()
