=============
EEG-ExPy
=============

*Democratizing the cognitive neuroscience experiment*

|badge_test| |badge_binder|

.. |badge_test| image:: https://github.com/NeuroTechX/eeg-expy/workflows/Test/badge.svg
   :target: https://github.com/NeuroTechX/eeg-expy/actions

.. |badge_binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/NeuroTechX/eeg-expy/master

.. image:: https://raw.githubusercontent.com/NeuroTechX/EEG-ExPy/master/doc/img/EEG-ExPy_Logo.png
   :align: center

EEG-ExPy is a collection of classic EEG experiments, implemented in Python. The experimental protocols and analyses are quite generic, but are primarily taylored for low-budget / consumer EEG hardware such as the InteraXon MUSE and OpenBCI Cyton. The goal is to make cognitive neuroscience and neurotechnology more accessible, affordable, and scalable. 

- **For an intro talk on the** *EEG-ExPy* **(formerly** *eeg-notebooks*) **project see:** `JG's Brainhack Ontario presentation <https://www.crowdcast.io/e/brainhack-ontario/7>`_.  
- **For documentation see:** `documentation site <https://neurotechx.github.io/eeg-expy/index.html>`_.
- **For code see:** `github site <https://github.com/neurotechx/eeg-expy>`_.
- **For instructions on running experiments see:** `running experiments <https://neurotechx.github.io/eeg-expy/getting_started/running_experiments.html>`_.
- **For instructions on initiating an EEG stream see:** `initiating an EEG stream <https://neurotechx.github.io/eeg-expy/getting_started/streaming.html>`_.
- **A series of tutorial videos will be coming soon!**  


----

**Note:** eeg-expy was previously known as eeg-notebooks. Before the renaming, eeg-notebooks also underwent major changes to the API in v0.2. The old v0.2 version, before the name change, is still available if you need it, in `this repo <https://github.com/neurotechx/eeg-notebooks_v0.2>`_. The even older v0.1 is also still available if needed `here <https://github.com/neurotechx/eeg-notebooks_v0.1>`_.

----


Overview
--------

Conventional lab-based EEG research typically uses research-grade (often high-density) EEG devices, dedicated stimulus delivery software and hardware, and dedicated technicians responsible for operating this equipment. The price tag for these items can easily extend into hundreds of thousands of dollars, which naturally places major limits on their acquisition and usage. 

In recent years, however, developments in hardware and software technologies are making it possible for many classic EEG cognitive neuroscience experiments to be conducted using a standard laptop/personal computer and a relatively cheap consumer-grade EEG device, with a combined minimum cost of less than 1000 dollars. This opens dramatic new possibilities for neurotechnology and cognitive neuroscience *education* (at both University and High School levels), as well as more ambitious and larger-scale *research* and *clinical* applications using large numbers of devices, and/or in more naturalistic (i.e. out-of-the-lab) settings. We like to think of this as contributing to the *democratization of the cognitive neuroscience experiment*.

The core aim of the EEG-Notebooks project is to provide the critical 'glue' that pulls together the various enabling technologies necessary for running these experiments and analyzing the data. This includes functionality for 

* streaming data from various relatively new wireless consumer-grade EEG devices  
* visual and auditory stimulus presentation, concurrent with and time-locked to the EEG recordings  
* a growing library of well-documented, ready-to-use, and ready-to-modify experiments 
* signal processing, statistical, and machine learning data analysis functionalities

A real one-stop-shop!

For more discussion on these social/scientific/technological contexts and trajectories, a) feel free to get in touch directly (see #Contact info below) and b) keep an eye out for the forthcoming eeg-expy research paper.


Documentation
-------------

The current version of eeg-expy is the 0.2.X series. The code-base and API are under major development and subject to change.

Check the `changelog <https://neurotechx.github.io/eeg-expy/changelog.html>`_ for notes on changes from previous versions.

**Installation instructions**, steps for **getting started**, common **troubleshooting** solutions and more can be found in the documentation for eeg-expy, available on the
`documentation site <https://neurotechx.github.io/eeg-expy/index.html>`_.

Acknowledgments
----------------

EEG-Notebooks was created by the `NeurotechX <https://neurotechx.com/>`_ hacker/developer/neuroscience community. The ininitial idea and majority of the groundwork was due to Alexandre Barachant - including the `muse-lsl <https://github.com/alexandrebarachant/muse-lsl/>`_ library, which is core dependency. Lead developer on the project is now `John Griffiths <www.grifflab.com>`_ . 

Key contributors include: Alexandre Barachant, Hubert Banville, Dano Morrison, Ben Shapiro, John Griffiths, Amanda Easson, Kyle Mathewson, Jadin Tredup, Erik Bjäreholt. 

Thanks also to Andrey Parfenov for the excellent `brainflow <https://github.com/brainflow-dev/brainflow/>`_ library, which has allowed us to dramatically expand the range of supporte devices; as well as the developers of `PsychoPy <https://github.com/psychopy/psychopy/>`_ and `MNE <https://github.com/mne-tools/mne-python/>`_, which together make up the central scaffolding of eeg-expy. 


Contribute
----------

This project welcomes and encourages contributions from the community!

If you have an idea of something to add to eeg-expy, please start by opening an
`issue <https://github.com/NeuroTechX/eeg-expy/issues/new/choose>`_.


Contact
-------------

The best place for general discussion on eeg-expy functionality is the `issues page <https://github.com/NeuroTechX/eeg-expy/issues/new/choose>`_. For more general questions and discussions, you can e-mail `john.griffiths@utoronto.ca`, or ping us on the `NeuroTechX Discord <https://discord.gg/zYCBfBf4W4>`_ or `NeuroTechX slack <https://neurotechx.herokuapp.com>`_.
