import numpy as np
import pytest

from eegnb.devices.eeg import EEG


class _StubBoard:
    def __init__(self, chunks):
        self._chunks = list(chunks)
        self.stopped = False
        self.released = False

    def get_board_data(self):
        return self._chunks.pop(0) if self._chunks else np.empty((4, 0))

    def stop_stream(self):
        self.stopped = True

    def release_session(self):
        self.released = True


def _eeg_with(chunks):
    eeg = EEG.__new__(EEG)
    eeg.backend = "brainflow"
    eeg.stream_started = True
    eeg.save_fn = None
    eeg._drained = []
    eeg.board = _StubBoard(chunks)
    return eeg


def test_draining_preserves_every_sample_in_order():
    a = np.arange(12, dtype=float).reshape(4, 3)
    b = np.arange(12, 20, dtype=float).reshape(4, 2)
    eeg = _eeg_with([a, b])
    eeg.drain_brainflow()
    eeg.drain_brainflow()
    np.testing.assert_array_equal(eeg._drained_data(),
                                  np.concatenate([a, b], axis=1))


def test_empty_reads_do_not_create_phantom_columns():
    a = np.arange(8, dtype=float).reshape(4, 2)
    eeg = _eeg_with([a, np.empty((4, 0))])
    eeg.drain_brainflow()
    eeg.drain_brainflow()
    assert eeg._drained_data().shape == (4, 2)


def test_nothing_drained_yields_an_empty_frame_not_a_crash():
    eeg = _eeg_with([])
    assert eeg._drained_data().size == 0
    eeg._write_brainflow_csv(eeg._drained_data())


def test_drain_is_a_no_op_before_the_stream_starts():
    eeg = _eeg_with([np.ones((4, 3))])
    eeg.stream_started = False
    eeg.drain_brainflow()
    assert eeg._drained == []


def test_drain_ignores_non_brainflow_backends():
    eeg = _eeg_with([np.ones((4, 3))])
    eeg.backend = "muselsl"
    eeg.drain()
    assert eeg._drained == []
