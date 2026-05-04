
try:
    #change the pref libraty to PTB and set the latency mode to high precision
    from psychopy import prefs
    prefs.hardware['audioLib'] = 'PTB'
    prefs.hardware['audioLatencyMode'] = 3
except ImportError:
    pass


from eegnb.devices.eeg import EEG
from typing import Optional

def get_experiments():
    from eegnb.experiments import VisualN170, Experiment
    from eegnb.experiments import VisualP300
    from eegnb.experiments import VisualSSVEP
    from eegnb.experiments import AuditoryOddball
    from eegnb.experiments.visual_cueing import cueing
    from eegnb.experiments.visual_codeprose import codeprose
    from eegnb.experiments.auditory_oddball import diaconescu
    from eegnb.experiments.auditory_ssaep import ssaep, ssaep_onefreq

    # New Experiment Class structure has a different initilization, to be noted
    return {
        "visual-N170": VisualN170,
        "visual-P300": VisualP300,
        "visual-SSVEP": VisualSSVEP,
        "visual-cue": cueing,
        "visual-codeprose": codeprose,
        "auditory-SSAEP orig": ssaep,
        "auditory-SSAEP onefreq": ssaep_onefreq,
        "auditory-oddball orig": AuditoryOddball,
        "auditory-oddball diaconescu": diaconescu,
    }


def get_exp_desc(exp: str):
    experiments = get_experiments()
    if exp in experiments:
        module = experiments[exp]
        if hasattr(module, "__title__"):
            return module.__title__  # type: ignore
    return "{} (no description)".format(exp)


def run_experiment(
    experiment: str, eeg_device: EEG, record_duration: Optional[float] = None, save_fn=None
):
    experiments = get_experiments()
    if experiment in experiments:
        exp_item = experiments[experiment]

        from eegnb.experiments import Experiment

        # Condition added for different run types of old and new experiment class structure
        # If it's a class (BaseExperiment subclass), instantiate it
        if isinstance(exp_item, type) and issubclass(exp_item, Experiment.BaseExperiment):
            # Concrete subclasses supply defaults for BaseExperiment's required args; mypy can't see which subclass.
            module = exp_item()  # type: ignore[call-arg]
            module.duration = record_duration
            module.eeg = eeg_device
            module.save_fn = save_fn
            module.run()
        else:
            # Otherwise it's an old-style module
            exp_item.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)  # type: ignore
    else:
        print("\nError: Unknown experiment '{}'".format(experiment))
        print("\nExperiment can be one of:")
        print("\n".join([" - " + exp for exp in experiments]))
