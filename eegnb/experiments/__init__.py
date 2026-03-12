from .visual_n170.n170 import VisualN170
from .visual_p300.p300 import VisualP300
from .visual_ssvep.ssvep import VisualSSVEP
from .semantic_n400.n400 import TextN400
# PTB does not yet support macOS Apple Silicon,
# this experiment needs to run as i386 if on macOS.
import sys

from psychopy import sound, plugins, prefs
import platform

# PTB does not yet support macOS Apple Silicon freely, need to fall back to sounddevice.
if platform.system() == 'Darwin' and platform.machine() == 'arm64':
    # import psychopy_sounddevice.backend_sounddevice
    plugins.scanPlugins()
    success = plugins.loadPlugin('psychopy-sounddevice')
    print(f"psychopy_sounddevice plugin loaded: {success}")

    # Force reload sound module
    import importlib
    importlib.reload(sound)
    # setting prefs.hardware['audio_device'] still falls back to a default device, need to use setDevice.
    audio_device = prefs.hardware.get('audioDevice', 'default')
    if audio_device and audio_device != 'default':
        sound.setDevice(audio_device)
else:
    #change the pref library to PTB and set the latency mode to high precision
    prefs.hardware['audioLib'] = 'PTB'
    prefs.hardware['audioLatencyMode'] = 3

from .auditory_oddball.aob import AuditoryOddball