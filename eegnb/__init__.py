from os import path, makedirs
from time import strftime, gmtime

DATA_DIR = path.join(path.expanduser('~/'),'.eegnb', 'data')


def generate_save_fn(board_name, experiment, subject_id, session_nb, data_dir=DATA_DIR):
    '''Generates a file name with the proper trial number for the current subject/experiment combo'''

    # convert subject ID to 4-digit number
    subject_str = 'subject%04.f' % subject_id
    session_str = 'session%03.f' % session_nb

    # folder structure is /DATA_DIR/experiment/site/subject/session/*.csv
    recording_dir = path.join(data_dir, experiment, 'local', board_name, subject_str, session_str)

    # check if directory exists, if not, make the directory
    if not path.exists(recording_dir):
        makedirs(recording_dir)

    # generate filename based on recording date-and-timestamp and then append to recording_dir
    save_fp = path.join(recording_dir, ("recording_%s" % strftime("%Y-%m-%d-%H.%M.%S", gmtime()) + ".csv"))

    return save_fp