
#change the pref libraty to PTB and set the latency mode to high precision
from psychopy import prefs
prefs.hardware['audioLib'] = 'PTB'
prefs.hardware['audioLatencyMode'] = 3


from eegnb.devices.eeg import EEG

from eegnb.experiments.visual_n170 import n170
from eegnb.experiments.visual_p300 import p300
from eegnb.experiments.visual_ssvep import ssvep
from eegnb.experiments.visual_cueing import cueing
from eegnb.experiments.visual_codeprose import codeprose
from eegnb.experiments.auditory_oddball import aob, diaconescu
from eegnb.experiments.auditory_ssaep import ssaep, ssaep_onefreq


experiments = {
    "visual-N170": n170,
    "visual-P300": p300,
    "visual-SSVEP": ssvep,
    "visual-cue": cueing,
    "visual-codeprose": codeprose,
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
        experiment: str, eeg_device: EEG, record_duration: float = None, save_fn=None, metadata_text: str=None):
    if experiment in experiments:
        module = experiments[experiment]
        module.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)  # type: ignore

        # Optional freeform metadata text for each saved data file
        if metadata_text:
            metadata_fn = save_fn.replace('.csv', '_metadata.txt')
            open(metadata_fn, 'w+').write(metadata_text)

    else:
        print("\nError: Unknown experiment '{}'".format(experiment))
        print("\nExperiment can be one of:")
        print("\n".join([" - " + exp for exp in experiments]))
