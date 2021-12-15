# NTCS Phase 1 Instructions

Important: Watch the instructional videos (link).

>Note: much of the info on this page will be familiar as it has probably been provided to you already. You should aim to read through all of the info here, but you **absolutely must** read [Step 6 'Run the visual N170 experiment']().


## Summary of the steps:

1. Register and run through the informed consent. 
2. Check your e-mail. This will give you a personalized link for uploading your recorded data. It will also give you these instructions.
3. Install miniconda
4. Set up your miniconda environment and install eeg-notebooks & dependencies
5. Setup your eeg-device (links to Muse, OpenBCI, Neurosity specific setups)
6. Run experiment using the script prompts
7. Find the recorded data on your local machine
8. Upload to the form via the personalized link from your first e-mail.


## Full step-by-step instructions

### 1. Sign up and provide informed consent.

### 2. Check your e-mail.

### 3. Install miniconda 

### 4. Set up environment and install eeg-notebooks

### 5. Set up your EEG Device

#### 5.1 Windows+Muse device users: install BlueMuse software

#### 5.2 OpenBCI users: install OpenBCI GUI

### 6. Run the visual N170 experiment

#### 6.1 Initiate an EEG stream

#### 6.2 Check your signal quality

#### 6.3 Run the experiment

The NTCS Phase 1 experiment is lasts approximately 1 hour.

When you are ready to begin proper data collection, you should ensure that you have sufficient time to complete (best to budget 1.5-2 hours), that you will not be interrupted during this time, and that you will be able to focus on the visual images presented on the screen with no distractions from your local environment. A small, quiet room such as an office or bedroom is ideal. 

The experiment consists of 10 short (5 minute) blocks, separated by short (~2 minute) rest periods. 

You are responsible for the timing of your rest periods and for initiating the next block on time after 2 minutes. 

To initiate a block, you will use the interactive command line prompt, where you should enter your device and subject information.

After the prompt questions are completed, the command line signal quality checker will be automatically launched. Take this opportunity if needed to adjust your device location on the head to maximize signal quality. 

The signal quality checker utility will cease when there are two successful 'good signal' evaluations, at which point you are good to go. 




eegnb runexp -ip muse2016





### 7. Locate and zip your recorded data

### 8. Upload your zipped data file to your personalized URL

### 9. Make use of your newfangled knowledge!






## FAQs, Troubleshooting, Gotchas

### Where are my files?

- they go into a hidden folder
- run the cmdline function

### How do I upload the files?

- run the zipper function
- the file will be x


### OpenBCI Ports and drivers

- ...

### OpenBCI Channel positions

- If 8 then X. If 4 then X. Do not use arbitrarily chosen channel locations. 
- 

### Python is not 3.7

- Don't use python 3.8. See anaconda installation command. 



