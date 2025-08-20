from os import path, makedirs
from time import strftime, gmtime
from pathlib import Path

DATA_DIR = path.join(path.expanduser("~/"), ".eegnb", "data")


def get_recording_dir(
    board_name: str,
    experiment: str,
    subject_id: int,
    session_nb: int,
    site="local",
    data_dir=DATA_DIR,
) -> Path:
    # convert subject ID to 4-digit number
    subject_str = f"subject{subject_id:04}"
    session_str = f"session{session_nb:03}"
    return _get_recording_dir(
        board_name, experiment, subject_str, session_str, site, data_dir=data_dir
    )


def _get_recording_dir(
    board_name: str,
    experiment: str,
    subject_str: str,
    session_str: str,
    site: str,
    data_dir=DATA_DIR,
) -> Path:
    """A subroutine of get_recording_dir that accepts subject and session as strings"""
    # folder structure is /DATA_DIR/experiment/board_name/site/subject/session/*.csv
    recording_dir = (
        Path(data_dir) / experiment / site / board_name / subject_str / session_str
    )

    # check if directory exists, if not, make the directory
    # Skip directory creation if wildcards are present (for pattern matching)
    if not any('*' in str(part) for part in [subject_str, session_str]) and not path.exists(recording_dir):
        makedirs(recording_dir)

    return recording_dir


def generate_save_fn(
    board_name: str,
    experiment: str,
    subject_id: int,
    session_nb: int,
    site="local",
    data_dir=DATA_DIR,
) -> Path:
    """Generates a file name with the proper trial number for the current subject/experiment combo"""
    recording_dir = get_recording_dir(
        board_name, experiment, subject_id, session_nb, site, data_dir=data_dir
    )

    # generate filename based on recording date-and-timestamp and then append to recording_dir
    return recording_dir / (
        "recording_%s" % strftime("%Y-%m-%d-%H.%M.%S", gmtime()) + ".csv"
    )
