|badge_test| |badge_binder|

.. |badge_test| image:: https://github.com/NeuroTechX/eeg-notebooks/workflows/Test/badge.svg
   :target: https://github.com/NeuroTechX/eeg-notebooks/actions

.. |badge_binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/NeuroTechX/eeg-notebooks/master

===================================================================
EEG-Notebooks - Democratizing the cognitive neuroscience experiment
===================================================================

.. image:: https://github.com/NeuroTechX/eeg-notebooks/raw/master/doc/img/eeg-notebooks_logo.png
   :width: 600
   :align: center

EEG-Notebooks is a collection of classic EEG experiments, implemented in Python 3 and Jupyter notebooks. The experimental protocols and analyses are quite generic, but are primarily taylored for low-budget / consumer EEG hardware such as the InteraXon MUSE and OpenBCI Cyton. The goal is to make cognitive neuroscience and neurotechnology more accessible, affordable, and scalable. 


- **For documentation see:** `documentation site <https://neurotechx.github.io/eeg-notebooks/index.html>`_.
- **For code see:** `github site <https://github.com/neurotechx/eeg-notebooks>`_.
- **For instructions on running experiments see:** `running experiments <https://neurotechx.github.io/eeg-notebooks/getting_started/running_experiments.html>`_.
- **For instructions on initiating an EEG stream see:** `initiating an EEG stream <https://neurotechx.github.io/eeg-notebooks/getting_started/streaming.html>`_.


----

*( Note: eeg-notebooks is now at version 0.2, with some major changes to the API and code base. The version 0.1 code is still available if you need it, in* `this repo <https://github.com/neurotechx/eeg-notebooks_v0.1>`_ )

----


Overview
--------

Conventional lab-based EEG research typically uses research-grade (often high-density) EEG devices, dedicated stimulus delivery software and hardware, and dedicated technicians responsible for operating this equipment. The price tag for these items can easily extend into hundreds of thousands of dollars, which naturally places major limits on their acquisition and usage. 

In recent years, however, developments in hardware and software technologies are making it possible for many classic EEG cognitive neuroscience experiments to be conducted using a standard laptop/personal computer and a relatively cheap consumer-grade EEG device, with a combined minimum cost of less than 1000 dollars. This opens dramatic new possibilities for neurotechnology and cognitive neuroscience *education* (at both University and High School levels), as well as more ambitious and larger-scale *research* and *clinical* applications using large numbers of devices, and/or in more naturalistic (i.e. out-of-the-lab) settings. We like to think of this as contributing to the *democratization of the cognitive neuroscience experiment*.

The core aim of the EEG-Notebooks project is to provide the critical 'glue' that pulls together the various enabling technologies necessary for running these experiments and analyzing the data. This includes functionality for 

- streaming data from various relatively new wireless consumer-grade EEG devices  
- visual and auditory stimulus presentation, concurrent with and time-locked to the EEG recordings  
- a growing library of well-documented, ready-to-use, and ready-to-modify experiments 
- signal processing, statistical, and machine learning data analysis functionalities

A real one-stop-shop!

For more discussion on these social/scientific/technological contexts and trajectories, a) feel free to get in touch directly (see #Contact info below) and b) keep an eye out for the forthcoming eeg-notebooks research paper.


Documentation
-------------

The current version of eeg-notebooks is the 0.2.X series. The code-base and API are under major development and subject to change.

Check the `changelog <https://neurotechx.github.io/eeg-notebooks/changelog.html>`_ for notes on changes from previous versions.

**Installation instructions**, steps for **getting started**, common **troubleshooting** solutions and more can be found in the documentation for eeg-notebooks, available on the
`documentation site <https://neurotechx.github.io/eeg-notebooks/index.html>`_.

Acknowledgments
----------------

EEG-Notebooks was created by the `NeurotechX <https://neurotechx.com/>`_ hacker/developer/neuroscience community. The ininitial idea and majority of the groundwork was due to Alexandre Barachant - including the `muse-lsl <https://github.com/alexandrebarachant/muse-lsl/>`_ library, which is core dependency. Lead developer on the project is now `John Griffiths <www.grifflab.com>`_ . 

Key contributors include: Alexandre Barachant, Hubert Banville, Dano Morrison, Ben Shapiro, John Griffiths, Amanda Easson, Kyle Mathewson, Jadin Tredup. 

Thanks also to Andrey Parfenov for the excellent

`brainflow <https://github.com/brainflow-dev/brainflow/>`_ library, which has allowed us to dramatically expand the range of supporte devices; as well as the developers of `PsychoPy <https://github.com/psychopy/psychopy/>`_ and `MNE <https://github.com/mne-tools/mne-python/>`_, which together make up the central scaffolding of eeg-notebooks. 


Contribute
----------

This project welcomes and encourages contributions from the community!

If you have an idea of something to add to eeg-notebooks, please start by opening an
`issue <https://github.com/neurotechx/eeg-notebooks/issues>`_.


Contact
-------------

The best place for general discussion on eeg-notebooks functionality is the  `Issues page <https://github.com/neurotechx/eeg-notebooks/issues>`_. For more general questions and discussions, you can e-mail `john.griffiths@utoronto.ca`, or ping us on the `NeuroTechX slack <https://neurotechx.herokuapp.com>`_.

