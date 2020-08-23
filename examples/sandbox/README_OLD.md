# EEG Notebooks


A collection of classic EEG experiments implemented in Python and Jupyter notebooks. This repo is a work in progress with the goal of making it easy to perform classical EEG experiments and automatically analyze data.

Currently, all experiments are implemented for the Muse EEG device and based on work done by Alexandre Barachant and Hubert Banville for the [muse-lsl](https://github.com/alexandrebarachant/muse-lsl) library. 

Please see the [documentation](http://eeg-notebooks.readthedocs.io/) for advanced installation instructions and complete info about the project.


## Getting Started


### Installation

If you are a Mac user, follow the installation instructions [here](MAC_INSTRUCTIONS.md)

You will need a Muse 2016 and Python installed on your computer. Psychopy, the stimulus presentation library that underlies most of the experiments, officially only supports Python 2. However, some users, especially those on Linux, have been able to work entirely in Python 3 without any issues.

`git clone https://github.com/neurotechx/eeg-notebooks`

Install all requirements.

`pip install -r requirements.txt`

See [here](http://eeg-notebooks.readthedocs.io/en/latest/setup_instructions_windows.html)
for more detailed setup instructions for windows operating systems.


### Running Experiments

Open the experiment you are interested in running in notebooks folder. Notebooks can be opened either with the Jupyter Notebook browser environment (run `jupyter notebook`) or in the [nteract](https://nteract.io/desktop) desktop application.

All experiments should be able to performed entirely within the notebook environment. On Windows 10, you will want to skip the bluetooth connection step and start an EEG data stream through the [BlueMuse](https://github.com/kowalej/BlueMuse) GUI.

*Note: if errors are encountered during viewing of the eeg data, try starting the viewer directly from the command line (`muselsl view`). Version 2 of the viewer may work better on Windows computers (`muselsl view -v 2`)

The basic steps of each experiment are as follows:
1. Open an LSL stream of EEG data.
2. Ensure that EEG signal quality is excellent and that there is very little noise. The standard deviation of the signal (displayed next to the raw traces) should ideally be below 10 for all channels of interest.
3. Define subject and session ID, as well as trial duration. *Note: sessions are analyzed independently. Each session can contain multiple trials or 'run-throughs' of the experiments.*
4. Simultaneously run stimulus presentation and recording processes to create a data file with both EEG and event marker data.
5. Repeat step 4 to collect as many trials as needed (4-6 trials of two minutes each are recommended in order to see the clearest results)
6. Load experimental data into an MNE Raw object.
7. Apply a band-pass filter to remove noise
8. Epoch the data, removing epochs where amplitude of the signal exceeded a given threshold (removes eye blinks)
9. Generate averaged waveforms from all channels for each type of stimulus presented

Notebooks in the `old_notebooks` folder only contain the data analysis steps (6-9). They can be used by using the `run_experiments.py` script (e.g `python run_eeg_experiment.py Auditory_P300 15 1`)

Currently available experiments: 
- N170 (Faces & Houses)
- SSVEP
- Visual P300
- Cueing (Kyle Mathewson)
- Baseline (Kyle, Eye's Open vs. Closed, needs notebook made)