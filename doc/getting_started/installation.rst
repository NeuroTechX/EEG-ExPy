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

- `Muse 2016`, `Muse 2`, and `Muse S` recordings on **Mac** require a BLED112 dongle (see below). The BLED112 dongle bypasses the native bluetooth hardware, which is not compatible with `muse` device streaming.

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

           conda create -n "eeg-expy" python=3.8 git pip

           conda activate "eeg-expy"

           git clone https://github.com/NeuroTechX/eeg-expy

           cd eeg-expy
           
           pip install -e .


    .. tab:: Virtualenv

       .. tabs::

          .. tab:: Windows

             .. code-block:: bash

                 mkdir eegnb_dir

                 python3 -m venv eegnb-env

                 git clone https://github.com/NeuroTechX/eeg-expy

                 eegnb-env\Scripts\activate.bat

                 cd eeg-notebooks

                 pip install -e .

          .. tab:: Linux or MacOS

             .. code-block:: bash

                 mkdir eegnb_dir

                 python3 -m venv eegnb-env

                 git clone https://github.com/NeuroTechX/eeg-expy

                 source eegnb-env/bin/activate

                 cd eeg-notebooks

                 pip install -e .



**Add the new environment to the jupyter kernel list**

For some operating systems, it is necessary the following command is necessary in order to make the new `eeg-expy` environment available from the jupyter notebook landing page


.. code-block:: bash

   python -m ipykernel install --user --name eeg-expy



**Test installation**

Start a jupyter notebooks session and you will be presented with the eeg-notebooks file structure. You can test the installation by opening a new jupyter notebook and running a cell containing the code below. This will run one session of the Visual N170 with your board of choice.

.. code-block:: python

   # Imports
   import os
   from eegnb import generate_save_fn
   from eegnb.devices.eeg import EEG
   from eegnb.experiments.visual_n170 import n170
   from eegnb.analysis.utils import load_data

   # Define some variables
   board_name = 'muse'
   # board_name = 'cyton'
   experiment = 'visual_n170'
   session = 999
   subject = 999 # a 'very British number'
   record_duration=120

   # Initiate EEG device
   eeg_device = EEG(device=board_name)

   # Create output filename
   save_fn = generate_save_fn(board_name, experiment, subject)

   # Run experiment
   n170.present(duration=record_duration, eeg=eeg_device, save_fn=save_fn)

   # Load recorded data
   raw = load_data(subject, session, board_names, experiment)


MUSE Requirements
======================

The InteraXon MUSE streams EEG over bluetooth. There are additional hardware and software requirements for making recordings with MUSE devices, which are different across operating systems.


MUSE recordings on windows: BlueMuse
-------------------------------------

BlueMuse is a Windows 10 program that allows communication between a Muse headband and a computer’s native bluetooth drivers using the LSL communication protocol. To install, go the the `BlueMuse github repo <https://github.com/kowalej/BlueMuse>`_ and follow the installation instructions.


MUSE recordings on Mac: BLED112 Dongle
---------------------------------------------

Unfortunately, the native bluetooth driver on Mac cannot be used with eeg-notebooks. To run on this operating system, it is necessary to purchase a `BLED112 USB Dongle <https://www.silabs.com/wireless/bluetooth/bluegiga-low-energy-legacy-modules/device.bled112/>`_. Note: this is a 'special' bluetooth dongle; standard bluetooth dongles will not work.


MUSE recordings on Linux
---------------------------------------------

Streaming MUSE data on Linux works without a dongle (which relies on `pygatt`'s `GATT` backend), but might be more stable with the `BLED112 USB Dongle` and `BGAPI` backend.


Issues
=================================

Common Problems
--------------------------------
**Problems with Conda and Jupyter Notebook:**
If you have created the conda env but it is not appearing as a kernel option in the jupyter notebook, you may need to manually add the new conda env to the jupyter envs list

.. code-block:: shell

   $ conda activate eeg-notebooks
   $ pip install ipykernel
   $ python -m ipykernel install --user --name eeg-notebooks


In windows, if the above is causing errors, the following commands may help:

.. code-block:: shell

   $ conda install pywin32
   $ conda install jupyter
   $ conda install nb_conda
   $ conda install ipykernel


Bug reports
-----------

Please use the `Github issue tracker <https://github.com/neurotechx/eeg-notebooks/issues>`_
to file bug reports and/or ask questions about this project. When filing a bug report, please include the follwing information:
* Operating System.
* Device being used.
* Any error messages generated.
