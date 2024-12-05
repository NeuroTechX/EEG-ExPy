"""
Test script for the primary eeg-expy supported experiments

This does a minimal import and run of several experiments

It is not directly part of the CI test suite, but should be 
checked regularly manually across as many OS setups as possible. 

"""

#from eegnb.experiments import VisualN170, VisualP300, VisualSSVEP, AuditoryOddball

from eegnb.experiments.visual_n170.n170 import VisualN170
expt = VisualN170(duration=10)
expt.run()

from eegnb.experiments.visual_ssvep.ssvep import VisualSSVEP
expt = VisualSSVEP(duration=10)
expt.run()

from eegnb.experiments.visual_p300.p300 import VisualP300
expt = VisualP300(duration=10)
expt.run()


