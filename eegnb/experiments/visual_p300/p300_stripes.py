import numpy as np
from pandas import DataFrame
from psychopy import visual, core, event
from time import time, strftime, gmtime
from optparse import OptionParser
from pylsl import StreamInfo, StreamOutlet


def present(duration, subject, run):

    # create
    info = StreamInfo("Markers", "Markers", 1, 0, "int32", "myuidw43536")

    # next make an outlet
    outlet = StreamOutlet(info)

    markernames = [1, 2]

    start = time()

    n_trials = 2010
    iti = 0.4
    soa = 0.3
    jitter = 0.2
    record_duration = np.float32(duration)

    # Setup log
    position = np.random.binomial(1, 0.15, n_trials)

    trials = DataFrame(dict(position=position, timestamp=np.zeros(n_trials)))

    # graphics
    mywin = visual.Window(
        [1920, 1080], monitor="testMonitor", units="deg", fullscr=True
    )
    grating = visual.GratingStim(win=mywin, mask="gauss", size=40, sf=2)
    fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0, 0], sf=0, rgb=[1, 0, 0])

    for ii, trial in trials.iterrows():
        # inter trial interval
        core.wait(iti + np.random.rand() * jitter)

        # onset
        grating.phase += np.random.rand()
        pos = trials["position"].iloc[ii]
        grating.ori = 90 * pos
        grating.draw()
        fixation.draw()
        timestamp = time()
        outlet.push_sample([markernames[pos]], timestamp)
        mywin.flip()

        # offset
        core.wait(soa)
        fixation.draw()
        mywin.flip()
        if len(event.getKeys()) > 0 or (time() - start) > record_duration:
            break
        event.clearEvents()
    # Cleanup
    mywin.close()


def main():
    parser = OptionParser()

    parser.add_option(
        "-d",
        "--duration",
        dest="duration",
        type="int",
        default=120,
        help="duration of the recording in seconds.",
    )
    parser.add_option(
        "-s",
        "--subject",
        dest="subject",
        type="int",
        default=1,
        help="subject number: must be an integer",
    )
    parser.add_option(
        "-r",
        "--run",
        dest="run",
        type="int",
        default=1,
        help="run (session) number: must be an integer",
    )

    (options, args) = parser.parse_args()
    present(options.duration)
    present(options.subject)
    present(options.n)


if __name__ == "__main__":
    main()
