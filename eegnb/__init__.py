from os import path, makedirs
from time import strftime, gmtime
from pathlib import Path

DATA_DIR = path.join(path.expanduser("~/"), ".eegnb", "data")


def get_recording_dir(
    board_name: str,
    experiment: str,
    subject_id: int,
    session_nb: int,
    data_dir=DATA_DIR,
) -> Path:
    # convert subject ID to 4-digit number
    subject_str = "subject%04.f" % subject_id
    session_str = "session%03.f" % session_nb

    # folder structure is /DATA_DIR/experiment/site/subject/session/*.csv
    recording_dir = (
        Path(data_dir) / experiment / "local" / board_name / subject_str / session_str
    )

    # check if directory exists, if not, make the directory
    if not path.exists(recording_dir):
        makedirs(recording_dir)

    return recording_dir


def generate_save_fn(
    board_name: str,
    experiment: str,
    subject_id: int,
    session_nb: int,
    data_dir=DATA_DIR,
) -> Path:
    """Generates a file name with the proper trial number for the current subject/experiment combo"""
    recording_dir = get_recording_dir(
        board_name, experiment, subject_id, session_nb, data_dir=DATA_DIR
    )

    # generate filename based on recording date-and-timestamp and then append to recording_dir
    return recording_dir / (
        "recording_%s" % strftime("%Y-%m-%d-%H.%M.%S", gmtime()) + ".csv"
    )
