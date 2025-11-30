# psychopy-sounddevice

Audio playback backend using the [SoundDevice](https://python-sounddevice.readthedocs.io) library.

## Installing

Install this package with the following shell command:: 

    pip install psychopy-sounddevice

You may also use PsychoPy's builtin package manager to install this package.

## Usage

Once the package is installed, PsychoPy will automatically load it when started and make objects available within the
`psychopy.sound.backend_sounddevice` namespace. You can select the backend to use for a session by specifying 
`'sounddevice'` in "Hardware" > "audio library" prefs. 
