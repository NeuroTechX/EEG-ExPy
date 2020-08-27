************
Installation
************

EEG-Notebooks is a Python library. It runs on all major operating systems (Windows, Linux, Mac). 

If you do not have Python installed, or are not particularly familiar with using it, then we highly recommend downloading and installing the Miniconda(3) Python(3) distribution. For users who prefer to use `VirtualEnv`  (`venv`) than `conda` for Python environment management, we provide equivalent installation and usage instructions where relevant. 


The principal purpose of EEG-Notebooks is to allow users to run and create cognitive neuroscience experiments using consumer-grade EEG systems. A secondary, complementary, purpose of the tool is to provide various functionalities for the organization, analysis and visualization of the data collected in these experiments. 

As such, there are two principal modes of usage:

1. Making new EEG recordings, and analyzing the newly recorded data

2. Not making EEG recordings, and analyzing existing (either previously recorded or public-domain) data


As may be expected, the installation and setup steps for mode 2 are simpler than mode 1, with the difference being additional hardware and software requirements for measuring, streaming and recording EEG data. These requirements, which are device- and operating system-specific, are as follows:

- `Muse 2016`, `Muse 2`, and `Muse S` recordings on **Windows** require the third-party streaming tool `BlueMuse`. `Bluemuse` deals with establishing a connection between the eeg device and the stimulus-delivery laptop/desktop. 

- `Muse 2016`, `Muse 2`, and `Muse S` recordings on **Linux** and **Mac** require a BLED112 dongle (see below). The BLED112 dongle bypasses the native bluetooth hardware, which is not compatible with `muse` device streaming. 

- `OpenBCI` recordings work the same for all operating systems, and do not require any additional hardware or software. 

- 'Usage mode 2' above (no EEG recordings) can be done easily on any operating system without any extra hardware or software, as well as on free temporary cloud compute servers through `Binder` and `GoogleColab`, which we provide instructions for. 



Installing the Python library
===============================

We highly recommend making use of a virtual environment (either `conda` or `virtualenv`) when installing eeg-notebooks.

If you don't already have a Python installation, grab the latest `miniconda` version for your operating system from here (https://docs.conda.io/en/latest/miniconda.html).

Use the following commands to download the repo, create and activate a conda or virtualenv virtual environment:


.. tabs::

    .. tab:: Conda

       .. code-block:: bash

           conda create -n "eeg-notebooks"

           conda activate "eeg-notebooks"

           pip install git

           git clone https://github.com/neurotechhx/eeg-notebooks

           cd eeg-notebooks

           pip install -r requirements.txt

            
 
    .. tab:: Virtualenv


       .. code-block:: bash

           conda create -n "eeg-notebooks"

           conda activate "eeg-notebooks"
 
           conda install git

           git clone https://github.com/neurotechhx/eeg-notebooks

           cd eeg-notebooks

           pip install -r requirements.txt


**Add the new environment to the jupyter kernel list**

For some operating systems, it is necessary the following command is necessary in order to make the new `eeg-notebooks` environment available from the jupyter notebook landing page


.. code-block:: bash

   python -m ipykernel install --user --name eeg-notebooks



**Test installation**

Start a jupyter notebooks session and you will be presented with the eeg-notebooks file structure. You can test the installation by opening a new jupyter notebook and running a cell containing the following


.. code-block:: python

   from eegnb.devices.eeg import EEG
   from eegnb.experiments.visual_n170 import n170

   # create eeg_device using the synthetic brainflow device
   eeg_device = EEG(device='synthetic')

   # run stimulus presentation for 20 seconds
   n170.present(duration=20, eeg=eeg_device)



MUSE Requirements
======================

The InteraXon MUSE streams EEG over bluetooth. There are additional hardware and software requirements for making recordings with MUSE devices, which are different across operating systems. 


MUSE recordings on windows: BlueMuse
-------------------------------------

BlueMuse is a Windows 10 program that allows communication between a Muse headband and a computer’s native bluetooth drivers using the LSL communication protocol. To install, go the the `BlueMuse github repo <https://github.com/kowalej/BlueMuse>`_ and follow the installation instructions.



MUSE recordings on Mac+Linux: BLED112 Dongle
---------------------------------------------

Unfortunately, the native bluetooth driver on Mac and Linux cannot be used with eeg-notebooks. To run on these operating systems, it is necessary to purchase a `BLED112 USB Dongle <https://www.silabs.com/wireless/bluetooth/bluegiga-low-energy-legacy-modules/device.bled112/>`_. Note: this is a 'special' bluetooth dongle; standard bluetooth dongles will not work. 

