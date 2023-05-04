
#change the pref libraty to PTB and set the latency mode to high precision
from psychopy import prefs
prefs.hardware['audioLib'] = 'PTB'
prefs.hardware['audioLatencyMode'] = 3


from eegnb.devices.eeg import EEG

from eegnb.experiments import VisualN170
#from eegnb.experiments import VisualN170_modified
from eegnb.summerschool import VisualN170_modified
#from eegnb.experiments import VisualP300
from eegnb.summerschool import VisualP300
from eegnb.experiments import VisualSSVEP
from eegnb.experiments import AuditoryOddball
from eegnb.experiments.visual_cueing import cueing
from eegnb.experiments.visual_codeprose import codeprose
from eegnb.experiments.auditory_oddball import diaconescu
from eegnb.experiments.auditory_ssaep import ssaep, ssaep_onefreq

NEW_EXP = "Summer School"
# New Experiment Class structure has a different initilization, to be noted
experiments = {
    "visual-N170": VisualN170(),
    "visual-P300": VisualP300(),
    "visual-SSVEP": VisualSSVEP(),
    "visual-cue": cueing,
    "visual-codeprose": codeprose,
    "auditory-SSAEP orig": ssaep,
    "auditory-SSAEP onefreq": ssaep_onefreq,
    "auditory-oddball orig": AuditoryOddball(),
    "auditory-oddball diaconescu": diaconescu,
    NEW_EXP: VisualN170_modified(),
}


def get_exp_desc(exp: str):
    if exp in experiments:
        module = experiments[exp]
        if hasattr(module, "__title__"):
            return module.__title__  # type: ignore
    return "{} (no description)".format(exp)


def run_experiment(
    experiment: str, eeg_device: EEG, record_duration: float = None, save_fn=None, my_img=None
):
    my_list = [NEW_EXP, "visual-N170", "visual-P300", "visual-SSVEP", "auditory-oddball orig"]
    if experiment in experiments:
        module = experiments[experiment]

        # Condition added for different run types of old and new experiment class structure
        if experiment in my_list:
            module.duration = record_duration
            module.eeg = eeg_device
            module.save_fn = save_fn
            module.run()
        else:
            module.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)  # type: ignore
    else:
        print("\nError: Unknown experiment '{}'".format(experiment))
        print("\nExperiment can be one of:")
        print("\n".join([" - " + exp for exp in experiments]))
