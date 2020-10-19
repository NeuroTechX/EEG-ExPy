
from .visual_n170 import n170
from .visual_p300 import p300
from .visual_ssvep import ssvep

def run_experiment(experiment, record_duration, eeg_device, save_fn):

    if experiment == 'visual-N170':
        n170.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)
    elif experiment == 'visual-P300':
        p300.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)
    elif experiment == 'visual-SSVEP':
        ssvep.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)

