import os

import numpy as np
import h5py

import eegnb
from . import aMMN

__title__ = "Auditory oddball (diaconescu)"


def makeoddball(inputs, rep):
    # based on inputs, creating oddball paradigms markers depending on "switch"
    value = inputs[0]
    count = 0
    markerArray = []
    for i in range(len(inputs)):
        if inputs[i] == value:
            count += 1
            if count == rep:
                markerArray.append(1)
            else:
                markerArray.append(3)
        else:
            if count == rep + 1:
                markerArray.append(2)

            else:
                markerArray.append(4)
            value = inputs[i]
            count = 1
    return markerArray


def maketonesnums(num):
    newArray = []
    for i in range(num):
        newArray.append(90000 + i)
    return newArray


def present(duration: int, eeg, save_fn: str):
    eegnb_dir = os.path.dirname(eegnb.__file__)
    mcond_file = os.path.join(
        eegnb_dir, "experiments", "auditory_oddball", "MUSE_conditions.mat"
    )

    F = h5py.File(mcond_file, "r")  # ['museEEG']
    highPE = np.squeeze(F["museEEG"]["design"]["highPE"][:]).astype(int)
    lowPE = np.squeeze(F["museEEG"]["design"]["lowPE"][:]).astype(int)
    inputs = np.squeeze(F["museEEG"]["design"]["inputs"][:]).astype(int)

    # based on inputs, creating oddball paradigms markers depending on "switch"
    tonenums = maketonesnums(1800)
    oddball3 = makeoddball(inputs, 3)
    oddball4 = makeoddball(inputs, 4)
    oddball5 = makeoddball(inputs, 5)
    oddball6 = makeoddball(inputs, 6)

    # modifying 0s in PE definitions of tones that represent markers to 3s to avoid loss of trials instead of ignoring them
    for i in range(len(highPE)):
        if highPE[i] == 0:
            highPE[i] = 3
        if lowPE[i] == 0:
            lowPE[i] = 3

    # 1 is standard/bottom, 2 is deviant/high, 3 is "baseline trial"

    stim_types = inputs
    itis = np.ones_like(inputs) * 0.5

    newAdditionalMarkers = []

    for i in range(0, len(highPE)):
        newAdditionalMarker = (
            str(oddball3[i])
            + str(oddball4[i])
            + str(oddball5[i])
            + str(oddball6[i])
            + str(highPE[i])
            + str(lowPE[i])
        )
        newAdditionalMarkers.append(newAdditionalMarker)

    aMMN.present(
        duration=duration,
        stim_types=stim_types,
        itis=itis,
        additional_labels={"labels": newAdditionalMarkers},
        eeg=eeg,
        save_fn=save_fn,
    )
