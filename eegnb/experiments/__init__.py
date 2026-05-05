class MissingExperiment:
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "PsychoPy is not installed. Stimulus presentation experiments "
            "are not available in this environment. Please install the "
            "'stimpres' or 'full' dependencies to use this feature."
        )

try:
    from .visual_n170.n170 import VisualN170
    from .visual_p300.p300 import VisualP300
    from .visual_ssvep.ssvep import VisualSSVEP
except ImportError:
    VisualN170 = MissingExperiment  # type: ignore
    VisualP300 = MissingExperiment  # type: ignore
    VisualSSVEP = MissingExperiment  # type: ignore

try:
    from psychopy import sound, plugins, prefs
    import platform
    import logging

    # PTB does not yet support macOS Apple Silicon freely, need to fall back to sounddevice.
    if platform.system() == 'Darwin' and platform.machine() == 'arm64':
        # import psychopy_sounddevice.backend_sounddevice
        plugins.scanPlugins()
        success = plugins.loadPlugin('psychopy-sounddevice')
        print(f"psychopy_sounddevice plugin loaded: {success}")

        # Force reload sound module
        import importlib
        importlib.reload(sound)
        
        # Try to set the audio device if requested and available
        audio_device = prefs.hardware.get('audioDevice', 'default')
        if audio_device and audio_device != 'default':
            if hasattr(sound, 'setDevice'):
                try:
                    sound.setDevice(audio_device)
                except Exception as e:
                    logging.warning(f"Failed to set audio device to '{audio_device}': {e}")
            else:
                logging.warning(f"sound.setDevice not available, could not set device to '{audio_device}'")
    else:
        #change the pref library to PTB and set the latency mode to high precision
        prefs.hardware['audioLib'] = 'PTB'
        prefs.hardware['audioLatencyMode'] = 3
except ImportError:
    import logging
    # logging.warning("PsychoPy not found. Stimulus presentation experiments will not be available.")
    pass

try:
    from .auditory_oddball.aob import AuditoryOddball
except ImportError:
    AuditoryOddball = MissingExperiment  # type: ignore
