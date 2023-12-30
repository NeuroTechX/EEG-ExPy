# Running Experiments
After you have installed the library there are two methods for collecting data. The first is using the command line tool with the flags detailed below. This is the easiest and recommended for users without much programming experience. The other method involves calling the experiment presentations from within a jupyter notebook (or custom python script).

## Command Line Interface
To activate the command line tool, open a command/terminal prompt and enter `eegnb runexp` followed by the appropriate flags for your device, desired experiment, and more. The possible flags are
* *-ed ; --eegdevice*: The device being used to record data. Each device has a specific string to be passed which can be seen on the [Initiating an EEG Stream](https://neurotechx.github.io/eeg-notebooks/getting_started/streaming.html) under the `EEG.device` parameter for the respective device.
* *-ex ; --experiment*: The experiment to be run
* *-ma ; --macaddr*: The MAC address of device to use (applicable devices e.g ganglion)
* *-rd ; --recdur*: Duration of recording (in seconds).
* *-of ; --outfname*: Save file name (this will be automatically generated to match default file system if left blank).
* *-ip ; --prompt*: Bypass the other flags to activate an interactive prompt.

### Using the introprompt flag
If using the `-ip` flag the user will be prompted to input the various session parameters. The prompts are detailed below.

```
eegnb runexp -ip
```

#### Board Selection
```
Welcome to NeurotechX EEG Notebooks. 
Please enter the integer value corresponding to your EEG device: 
[0] None 
[1] Muse2016 
[2] Muse2 
[3] OpenBCI Ganglion 
[4] OpenBCI Cyton 
[5] OpenBCI Cyton + Daisy 
[6] G.Tec Unicorn 
[7] BrainBit 
[8] Notion 1 
[9] Notion 2 
[10] Synthetic 

Enter Board Selection:
```
Here you specify which of the supported boards you are using to collect data. EEG Notebooks supports a number of different consumer boards with various backends. This step ensures that the proper backend and device parameters are used. **If you are using an OpenBCI board** there will be an additional prompt asking for the desired connection method. Right now it is recommended to use the USB dongle over the wifi shield.

#### Experiment Selection
```
Please select which experiment you would like to run: 
[0] Visual N170
[1] Visual P300
[2] Visual SSVEP
[3] visual-cue (no description)
[4] visual-codeprose (no description)
[5] Auditory SSAEP (orig)
[6] Auditory SSAEP (single freq)
[7] Auditory oddball (orig)
[8] Auditory oddball (diaconescu)

Enter Experiment Selection:
```
This section allows you to select one of the above experiments to run. There are other experiments available, however, they have not yet been updated for the new API to be device agnostic. As they get updated, more experiments will populate this section.


#### Recording Duration
```
Now, enter the duration of the recording (in seconds). 

Enter duration:
```
This is the duration of each recording. It is standard to use 120 second (2 minute) long recordings per recording, but some people might experience visual fatigue and difficulty not blinking for as long, so you are welcome to adjust length as needed.

#### Subject ID
```
Next, enter the ID# of the subject you are recording data from. 

Enter subject ID#:
```

#### Session Number
```
Next, enter the session number you are recording for. 

Enter session #:
```
The session number corresponds to each time you sit down to take multiple recordings. If you put your device on and run this script 5 consecutive times you would use the same session number every time. However, if you were to take a break then return for an additional 3 recordings, the last 3 would have a new session number. For more information about how this corresponds to saving data please see the documentation page on loading and saving data. 

If you are using **OpenBCI on Windows/MacOS** you will be given an additional prompt to enter the name of the serial port the USB dongle is using. For instructions on how to use the OpenBCI GUI to find the serial port see [Initiating an EEG Stream](https://neurotechx.github.io/eeg-notebooks/getting_started/streaming.html).



## Using Jupyter Notebooks or a custom script
The first step is to import all of the necessary library dependencies. These are necessary for generating a save file name which conforms to the default folder structure, streaming and recording EEG data, and running the stimulus presentation.

```python
from eegnb import generate_save_fn
from eegnb.devices.eeg import EEG
from eegnb.experiments.visual_n170 import n170
```

Next we need to define session parameters which are otherwise handled via input prompts in the run `run_notebooks.py` script. After we define the session parameters we will pass them to the file name generator.

```python
board_name = 'cyton'
experiment = 'visual_n170'
session = 1
subject = 1
record_duration = 120

# Create output filename
save_fn = generate_save_fn(board_name, experiment, subject, session)
```

Next it is necessary to call the `eegnb.devices.eeg.EEG` class which handles all of the backend processes related to each device.

```python
eeg_device = EEG(device=board_name)
```

Finally, we call the `present` method of the class corresponding to our desired experiment, in this case the visual N170. We pass both the EEG device and generated save file name in order to collect and save data. The presentation can also be run without an EEG device/save file for testing and debugging.

```python
n170.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)
```

All together the example script looks like
```python
# Imports
from eegnb import generate_save_fn
from eegnb.devices.eeg import EEG
from eegnb.experiments.visual_n170 import n170

# Define some variables
board_name = 'cyton'
experiment = 'visual_n170'
session = 1
subject = 1
record_duration = 120

# Create output filename
save_fn = generate_save_fn(board_name, experiment, subject, session)

# Setup EEG device
eeg_device = EEG(device=board_name)

# Run stimulus presentation
n170.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)
```


## Using virtual reality

For example, should be able to run the N170 stimulus on the headset and collect valid eeg data, then be able to analyze and visualize it afterwards.

Prerequisites:
* Oculus Rift compatible VR headset, e.g. Oculus Rift or Meta Quest series.
* Native Windows installation with meta link compatible video card.
* EEG device, e.g. OpenBCI Cyton or Muse

Example of steps used:
1. Modify experiment present argument to use vr eg:

```python
# Run stimulus presentation
n170.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn, use_vr=True)
```

2. Turn on and place the VR headset onto the head.
3. If it is your own head, enable passthrough to help with wearing the eeg device.
4. Place the EEG device on top of the head.
5. Ensure the electrodes are touching the scalp ok and not being blocked by the headset strap.
6. Connect the VR headset to the windows install, via air link or link cable.
7. Once the Oculus menu has finished loading on the VR headset, open the built-in Oculus desktop app by using the touch controllers or gamepad.
8. Try opening an eeg device raw data viwer and verify that the electrodes are receiving a good signal without too much noise, eg 'OpenBCI GUI'.
9. Run the EEG-ExPy experiment from the command line or IDE, it should load and take control from the Oculus desktop app.
10. Follow the experiment instructions, and press a key if necessary to begin the experiment and collect valid data.

### Other experiments can have VR added too.

1. Load/prepare stimulus in the same function as previously (def load_stimulus(self))
2. Present stimulus in the same function as previously(def present_stimulus(self, current_trial: int))
3. VR can be enabled for the experiment as part of the initializer to the base Experiment class, by default it is not enabled(use_vr=False) and will function the same as previously before VR functionality was added.

