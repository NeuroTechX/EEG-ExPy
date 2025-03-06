from .visual_n170.n170 import VisualN170
from .visual_p300.p300 import VisualP300
from .visual_ssvep.ssvep import VisualSSVEP

# PTB does not yet support macOS Apple Silicon,
# this experiment needs to run as i386 if on macOS.
import sys
import platform
if sys.platform != 'darwin' or platform.processor() != 'arm':
    from .auditory_oddball.aob import AuditoryOddball