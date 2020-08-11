**************
Code Changelog
**************

This page contains the changelog for eeg-notebooks and any notes on updating between versions.



0.2.X
======

The 0.2.X series included several major updates in api, backend, and compatibility. 
These updates were introduced around and for the OpenBCI-NTX Challenge 2020


Updates include:


- Support for OpenBCI EEG devices introduced through brainflow support

- Abstracted 'device' class introduced to cover both OpenBCI with brainflow and Muse with muse-lsl

- Subprocess calls for running concurrent psychopy and muselsl streams put inside functions (not required to be called by user)

- New sphinx gallery-based documentation site, built with sphinx and hosted on gh-pages

- General cleanup of documentation, installation, and setup instructions

- Example datasets removed from repo and placed in separate cloud storage

- Dataset downloader functions implemented

- Kyle Mathewson's visual cueing experiment + results added



0.1.X
======

The 0.1.X series was the initial port of the muse-lsl code, and development of the jupyter notebook-oriented approach. It was developed principally for the 2018/2019 NeuroBRITE and BrainModes programs. 





