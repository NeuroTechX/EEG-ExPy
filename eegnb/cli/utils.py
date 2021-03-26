from eegnb.devices.eeg import EEG

from eegnb.experiments.visual_n170 import n170
from eegnb.experiments.visual_p300 import p300
from eegnb.experiments.visual_ssvep import ssvep
from eegnb.experiments.auditory_oddball import aob, diaconescu
from eegnb.experiments.auditory_ssaep import ssaep, ssaep_onefreq


experiments = {
    "visual-N170": n170,
    "visual-P300": p300,
    "visual-SSVEP": ssvep,
    "auditory-SSAEP orig": ssaep,
    "auditory-SSAEP onefreq": ssaep_onefreq,
    "auditory-oddball orig": aob,
    "auditory-oddball diaconescu": diaconescu,
}


def get_exp_desc(exp: str):
    if exp in experiments:
        module = experiments[exp]
        if hasattr(module, "__title__"):
            return module.__title__  # type: ignore
    return "{} (no description)".format(exp)


def run_experiment(
    experiment: str, eeg_device: EEG, record_duration: float = None, save_fn=None
):
    if experiment in experiments:
        module = experiments[experiment]
        module.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)  # type: ignore
    else:
        print("\nError: Unknown experiment '{}'".format(experiment))
        print("\nExperiment can be one of:")
        print("\n".join([" - " + exp for exp in experiments]))
