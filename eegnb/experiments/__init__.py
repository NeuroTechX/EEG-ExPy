from typing import TYPE_CHECKING

from eegnb.utils.missing import missing_class

MissingExperiment = missing_class(
    "PsychoPy",
    "Stimulus presentation experiments",
    "stimpres",
)

if TYPE_CHECKING:
    from .visual_n170.n170 import VisualN170
    from .visual_p300.p300 import VisualP300
    from .visual_ssvep.ssvep import VisualSSVEP
else:
    try:
        from .visual_n170.n170 import VisualN170
        from .visual_p300.p300 import VisualP300
        from .visual_ssvep.ssvep import VisualSSVEP
    except ImportError:
        VisualN170 = MissingExperiment
        VisualP300 = MissingExperiment
        VisualSSVEP = MissingExperiment

try:
    from psychopy import prefs

    prefs.hardware['audioLib'] = 'PTB'
    prefs.hardware['audioLatencyMode'] = 3
except ImportError:
    import logging
    # logging.warning("PsychoPy not found. Stimulus presentation experiments will not be available.")
    pass

if TYPE_CHECKING:
    from .auditory_oddball.aob import AuditoryOddball
else:
    try:
        from .auditory_oddball.aob import AuditoryOddball
    except ImportError:
        AuditoryOddball = MissingExperiment
