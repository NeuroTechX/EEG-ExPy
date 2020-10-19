import argparse
import sys
from .cli import CLI


def main():
    parser = argparse.ArgumentParser(
        description="eeg-notebooks command line interface",
        usage='''eegnb <command> [<args>]

    Available commands:
    ===================

    runexp      Run experiment
    ------
                
                Options:

                -ed --eegdevice    EEG device
                -ex --expt         Experiment to run
                -rd --recdur       Recording duration
                -of --outfname     Output filename
                -ip --inprom       Use input prompt 


                Examples:

                Run experiment explicitly defining all necessary parameters 
                (eeg device, experiment, duration, output file)
                This is the quickest way to run eeg-notebooks experiments, 
                but requires knowledge of formatting for available options

                $ eegnb runexp -ed blah -ex visual-N170 -rd 120 -of test.csv 
                

                Launch the interactive command line experiment setup+run tool
                This takes you through every experiment parameter in order 
                and figures out + runs the complete function calls for you

                $ eegnb runexp -ip




    view        View live eeg stream
    ----

                Options:

                -ed --device       EEG device
                -vt --version      Viewer version (for muselsl)

                
                Examples:





    ''')

    parser.add_argument('command', help='Command to run.')

    # parse_args defaults to [1:] for args, but you need to
    # exclude the rest of the args too, or validation will fail
    args = parser.parse_args(sys.argv[1:2])

    if not hasattr(CLI, args.command):
        print('Incorrect usage. See help below.')
        parser.print_help()
        exit(1)

    cli = CLI(args.command)


if __name__ == '__main__':
    main()
