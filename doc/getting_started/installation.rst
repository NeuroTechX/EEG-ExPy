************
Installation
************


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

