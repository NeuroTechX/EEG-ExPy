"""

ABOUT
======

This is a short test script for the primary eeg-expy supported experiments.

It is intended as a quick manual test that everything is in working order with the eeg-expy installation. 

( Note that it is far from comprehensive in that regard, however. More coverage and comprehensiveness will be added, primarily if/when it becomes useful to the eeg-expy developers )

This does a minimal import and run of several experiments

Note that although this is a .py file in the `tests` folder, it is not directly part of the CI test suite, which is designed around the github CI and sphinx-gallery docs build side of things. 

The reason for this is that it is not straightforward to incorporate tests of EEG device data streaming (which cannot be done in the cloud) or stimulus presentation in to the github CI. And in any case, both of these are highly dependent on the hardware being used (OS and specs of the computer running eeg-expy, the EEG device, etc.). 

So this script serves as a separate line of installation tests. 

If you are using eeg-expy, and especially if you are a developer / contributor / general technically savvy person, this script should be used regularly to check things are working ok. It should be checked, and info fed back via the github repo, on as many OS and device setup configurations as possible. 


USAGE:
=======

Currently this script is very minimal. 

At some point we will likely make it a bit more structured wrt options etc. 

The high-level usage instruction is: 

1. COPY THIS SCRIPT
2. EDIT THE COPY
3. RUN THE EDITED COPY

(because if you edit the original script then you will have issues when updating the library with `git pull`)

Your edits should be restricted to the config dict at the top. 

The key parts of this are 

- Auditory device configuration
- EEG device and bluetooth streaming configuration (not yet implemented)

You may need to do some trial-and-error testing to identify the correct info to add there. 

Relying on default configurations and automatically detected parameters is not recommended


"""

from psychopy import prefs, sound

test_config = dict(run_n170 = True,
                   run_p300 = True,
                   run_ssvep = True,
                   run_aob = True,
                   audio_device = prefs.hardware['audioDevice'],
                   audio_lib = prefs.hardware['audioLib'],
                   test_duration = 10,
                   fullscreen = False
                   )
# -----------------------------------------------------------------------
# ***EDIT THIS SECTION ONLY*** to specify any non-default config entries
test_config['audio_device'] = 'MacBook Pro Speakers' # see `sound.getDevices()`
test_config['audio_lib'] = 'sounddevice'
# ----------------------------------------------------------------------

# ---------------------------------------
# CONFIG NOTES:
#
# - Windows 11 on iMAC (through bootcamp): 
#       test_config['audio_device'] = "Speakers (Apple Audio Device)"
#       test_config['audio_lib'] = 'ptb'
#
# ---------------------------------------

# ---------------------------------------
# CONFIG NOTES:
#
# - macOS 15.5 on Macbook Pro M1 (through bootcamp):
#     test_config['audio_device'] = 'MacBook Pro Speakers'
#     test_config['audio_lib'] = 'sounddevice'
#
# ---------------------------------------

tc = test_config

d = tc['test_duration']


if tc['run_n170']:
    from eegnb.experiments.visual_n170.n170 import VisualN170
    expt = VisualN170(duration=d)
    expt.use_fullscr = tc['fullscreen']
    expt.run()

if tc['run_p300']:
    from eegnb.experiments.visual_p300.p300 import VisualP300
    expt = VisualP300(duration=d)
    expt.use_fullscr = tc['fullscreen']
    expt.run()

if tc['run_ssvep']: 
    from eegnb.experiments.visual_ssvep.ssvep import VisualSSVEP
    expt = VisualSSVEP(duration=d)
    expt.use_fullscr = tc['fullscreen']
    expt.run()

if tc['run_aob']:
    # prefs need to be set before importing eegnb.experiments, otherwise the default audio device will be used for the 'sounddevice' lib.
    prefs.hardware['audioDevice'] = tc['audio_device']
    prefs.hardware['audioLib'] = tc['audio_lib']
    from eegnb.experiments.auditory_oddball.aob import AuditoryOddball

    # sound.getDevices() will fail for sounddevice lib until eegnb.experiments is imported.
    assert tc['audio_device'] in sound.getDevices()

    expt = AuditoryOddball(duration=d)
    expt.use_fullscr = tc['fullscreen']
    expt.run()



