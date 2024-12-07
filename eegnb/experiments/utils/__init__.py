from dataclasses import dataclass

@dataclass
class TrialParams:
    """
    Encapsulates parameters for defining trials in EEG experiments.

    This dataclass provides a structured way to define and manage trial-specific
    parameters, particularly timing information, for EEG studies. It's designed
    to be flexible enough for use in various experimental paradigms, including
    but not limited to event-related designs.

    Attributes:
        iti (float): Inter-Trial Interval, in seconds. The base time between
                     the end of one trial and the beginning of the next.
        jitter (float): Maximum random time, in seconds, added to the ITI.
                        Used to prevent anticipatory responses and increase
                        design efficiency in event-related paradigms.
        soa (float): Stimulus On Arrival, in seconds. The duration the
                     stimulus is shown for until the trial ends.
        n_trials (int): The total number of trials in the experiment.

    Example:
        # Create parameters 1s ITI, up to 0.2s jitter, and 0.5s SOA for 100 trials.
        params = TrialParams(iti=1.0, jitter=0.2, soa=0.5, n_trials=100)
    """

    iti: float
    jitter: float
    soa: float
    n_trials: int
