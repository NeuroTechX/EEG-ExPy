

import sys
from multiprocessing import Process
from time import strftime, gmtime

def run_experiment(expt_name, subj_num='', sess_num='', muse_lsl_dir='muse-lsl'):

    if 'Visual_P300' in expt_name:
        from stimulus_presentation import visual_p300 as expt_function

    elif 'Visual_N170' in expt_name:
        from stimulus_presentation import n170 as expt_function

    elif 'SSVEP' in expt_name:
        from stimulus_presentation import ssvep as expt_function

    elif 'SSAEP' in expt_name:
        from stimulus_presentation import ssaep as expt_function

    elif 'Auditory_P300' in expt_name:
        from stimulus_presentation import auditory_p300 as expt_function

    expt_args = []
    record_args = []

    if 'test' in expt_name:
        expt_args.append(20)
        record_args.append(20)
    else:
        expt_args.append(120)
        record_args.append(120)

    file_name = expt_name + "_subject" + str(subj_num) + "_session" + str(
        sess_num) + "_" + strftime("%Y-%m-%d-%H.%M.%S", gmtime()) + ".csv"
    record_args.append(file_name)

    expt_process = Process(target=expt_function.present, args=expt_args)
    record_process = Process(target=expt_function.present, args=record_args)

    expt_process.start()
    record_process.start()


if __name__ == '__main__':

    """
    Usage:

    python run_eeg_experiment.py EXPT_NAME SUBJECT_NUM SESS_NUM 


    Experiment names:

    'Visual_N170'
    'Visual_P300'
    'SSVEP'
    'SSAEP'
    'Auditory_P300'

    Add '_test' to the end of the experiment name to run a quick (20s) version


    Examples:

    python run_experiment.py N170 


    python run_experiment.py mlsl_SSVEP_test


    """

    expt_name = sys.argv[1]

    if len(sys.argv) == 4:
        subj_num, sess_num = sys.argv[2:4]
    else:
        subj_num = ''
        sess_num = ''

    run_experiment(expt_name, subj_num, sess_num)
