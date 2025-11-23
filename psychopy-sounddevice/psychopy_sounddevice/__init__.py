#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Originally from the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Audio backend for playback using SoundDevice.
"""

__version__ = '0.0.1'

from .backend_sounddevice import (
    init,
    getDevices,
    getStreamLabel,
    SoundDeviceSound)

