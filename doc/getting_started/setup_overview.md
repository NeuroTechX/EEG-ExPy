# Setup Overview

Here is a high-level overview of the installation and setup steps that will take you from complete scratch to running experiments and collecting data with eeg-notebooks.

## 1. Install Miniconda & set up your virtual environment
Miniconda makes it easy to manage multiple different Python installations on the same machine. While using miniconda environments is not required, we strongly recommend it. 
Follow installation instructions [here](https://docs.conda.io/en/latest/miniconda.html).


## 2. Clone EEG-Notebooks and install dependencies
To install eeg-notebooks and run the experiments you will need a terminal with Python access. The miniconda terminal instlled in Step 1 is ideal and preferable for this, although advanced users are welcome to use alternative options. The following is specific to miniconda:


Open the terminal  
`cd` to the directory you want to clone the eeg-notebooks code folder to  
`conda create -n "eeg-notebooks" Python=3`     
`conda activate eeg-notebooks`    
`conda install git`  
`git clone https://github.com/neurotechx/eeg-notebooks`    
`cd eeg-notebooks`    
`pip install -e .`    

For further information on this, see the [installation instructions page](https://neurotechx.github.io/eeg-notebooks/getting_started/installation.html#installing-the-python-library) in the eeg-notebooks documentation.


## 3. Connect your EEG device

Currently, eeg-notebooks can be used with the following EEG devices:

- InteraXon Muse2016/Muse2/MuseS  
- OpenBCI Ganglion/Cyton    
- G.Tec Unicorn   
- BrainBit    
- Neurosity Notion1/Notion2  

The connection process differs depending on both the device and operating system you are using. 


***3a. : OpenBCI ***

***3b. : Muse on Windows ***

***3c.: Muse on Linux/Mac ***

## 4. Run EEG experiments & collect data
EEG-Notebooks contains a script file called `run_notebooks.py` which provides prompts to guide you through running each type of experiment. 
