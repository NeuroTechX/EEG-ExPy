import logging
import sys
import pytest
from unittest.mock import patch, MagicMock
from brainflow.board_shim import BrainFlowError
from eegnb.devices.eeg import EEG


def test_cli_import_does_not_eagerly_import_psychopy():
    """Ensure CLI startup defers PsychoPy/GUI imports until needed, avoiding Windows COM STA conflicts with BLE."""
    for mod in list(sys.modules):
        if mod in ("eegnb.cli.__main__", "eegnb.analysis.streaming_utils", "psychopy"):
            sys.modules.pop(mod, None)

    import eegnb.cli.__main__  # noqa: F401

    assert "eegnb.analysis.streaming_utils" not in sys.modules
    assert "psychopy" not in sys.modules


def test_brainflow_prepare_session_failure_logs_and_releases(caplog):
    """Verify clear diagnostic logging and session cleanup when BrainFlow prepare_session fails."""
    mock_board = MagicMock()
    mock_board.prepare_session.side_effect = BrainFlowError("unable to prepare streaming session", 7)
    mock_board.is_prepared.return_value = True

    with patch("eegnb.devices.eeg.BoardShim", return_value=mock_board) as mock_shim_cls:
        mock_shim_cls.get_sampling_rate.return_value = 256
        with caplog.at_level(logging.ERROR):
            with pytest.raises(BrainFlowError):
                EEG(device="muse2_bfn")

    assert "Failed to prepare BrainFlow session for device 'muse2_bfn'" in caplog.text
    mock_board.release_session.assert_called_once()
