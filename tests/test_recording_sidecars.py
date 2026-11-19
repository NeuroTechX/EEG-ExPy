import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from eegnb import is_sidecar

RECORDING = "recording_2026-11-09-05.58.13"
CHANNELS = ["Fz", "C3", "Cz", "C4", "Pz", "PO7", "Oz", "PO8",
            "F5", "F7", "F3", "F1", "F2", "F4", "F6", "F8"]


@pytest.mark.parametrize("name", [f"{RECORDING}_timing.csv", f"{RECORDING}_session.json"])
def test_files_written_beside_a_recording_are_sidecars(name):
    assert is_sidecar(name)
    assert is_sidecar(Path("data") / "session001" / name)


@pytest.mark.parametrize("name", [f"{RECORDING}.csv",
                                  "subject309_session2_recording_2018-11-22-17.48.17.csv",
                                  "data_2018-05-14-19.38.10.csv", "my_session.csv",
                                  f"{RECORDING}_session.csv", f"{RECORDING}_timing.json"])
def test_recordings_are_not_sidecars(name):
    assert not is_sidecar(name)


def _session_folder(folder, n_samples=500):
    folder.mkdir(parents=True)
    columns = ["timestamps"] + CHANNELS + ["stim"]
    data = np.zeros((n_samples, len(columns)))
    data[:, 0] = np.arange(n_samples) / 250.0
    pd.DataFrame(data, columns=columns).to_csv(folder / f"{RECORDING}.csv", index=False)
    (folder / f"{RECORDING}_timing.csv").write_text(
        "trial_idx,software_time,submitted_frame_index\n0,1.0,1\n")
    (folder / f"{RECORDING}_session.json").write_text(
        json.dumps({"completed": True, "reason": None}))


def test_load_data_loads_the_recording_and_skips_its_sidecars(tmp_path):
    pytest.importorskip("mne")
    from eegnb.analysis.utils import load_data
    _session_folder(tmp_path / "visual-N170" / "local" / "synthetic" / "subject0001" / "session001")
    raw = load_data(1, 1, "synthetic", "visual-N170", data_dir=str(tmp_path), verbose=0)
    assert raw.n_times == 500


@pytest.mark.parametrize("subjects, sessions, folders", [
    ("all", "all", ("subject1", "session1")),
    ([1], [1], ("subject001", "session01")),
], ids=["all", "one"])
def test_fetch_dataset_lists_only_recordings(tmp_path, subjects, sessions, folders):
    pytest.importorskip("gdown")
    from eegnb.datasets.datasets import fetch_dataset
    folder = tmp_path.joinpath("visual-N170", "eegnb_examples", "muse2016", *folders)
    _session_folder(folder, n_samples=2)
    fnames = fetch_dataset(data_dir=str(tmp_path), experiment="visual-N170",
                           subjects=subjects, sessions=sessions)
    assert [Path(f).name for f in fnames] == [f"{RECORDING}.csv"]
