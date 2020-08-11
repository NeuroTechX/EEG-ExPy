********************************
_
*********************************

Visual SSVEP
=====================

The steady-state visual evoked potential (SSVEP) is a repetitive evoked potential that is naturally produced when viewing stimuli flashing between a range of 6-75hz. Electrical activity at the same frequency as the visual stimulation can be detected in the occipital areas of the brain, likely due to the perceptual recreation of the stimulus in the primary visual cortex.

The SSVEP is often used in BCI applications due to its ease of detection and the amount of information that a user can communicate due to the high potential frequency resolution of the SSVEP.

In this notebook, we will use the Muse EEG headband with an extra occipital electrode to detect the SSVEP and evaluate it’s use in SSVEP-based BCIs.


Extra Electrode

Although the SSVEP is detectable at the default temporal electrodes, it can be seen much more clearly directly over the occipital cortex.

The Muse 2016 supports the addition of an extra electrode which can be connected through the devices microUSB charging port.

Instructions on how to build an extra electrode for Muse
Working with the extra electrode
For this experiment, the extra electrode should be placed at POz, right at the back of the skull. It can be secured in place with a bandana or a hat


**SSVEP Experiment Notebook Examples**

.. include:: ../auto_examples/visual_ssvep/index.rst 


