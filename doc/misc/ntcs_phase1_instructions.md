# NTCS Phase 1 Instructions

Welcome to the `NeuroTech Challenge Series (NTCS), Phase 1` instructions page. 

`NTCS Phase 1` is an international citizen science research study, run by researchers at the University of Toronto and the Centre for Addiction and Mental Health (CAMH), in collaboration with OpenBCI, NeuroTechX, and the eeg-notebooks core developer team. 

If this is the first time you are learning about NTCS, check out the [NTCS website](https://neurotech-challenge.com/) for additional info about this and other upcoming challenges and opportunities. 

If you are ready to get going with NTCS Phase 1, have been directed here by other comms from us, or would simply like to browse through to getter a better idea of what's involved, you are in the right place. 

These instructions, and NTCS in general, also double up as an excellent practical introduction to the `eeg-notebooks` software. 

Have fun and thank you for joining on NTCS Phase 1!


## Instructional Videos

We recommend that before you get going on the steps listed below, you watch the instructional videos. 

Video 1 is a short general overview and big picture. You should watch this fully first before continuing. 

Videos 2-5 include live demos and discussions showing you the specific steps you need to follow, and what to expect when you run them. For these, it is probably best to go back and forth a bit between the instructions text below and stepping through sections carefully, as needed. 

- [Video 1](): About NTCS
- [Video 2](): Installing the software
- [Video 3](): Initiating an EEG stream
- [Video 4](): Running the experiment
- [Video 5](): Uploading your data. 

Additionally, you might be interested to check out JG's [introductory lecture on eeg-notebooks](https://www.youtube.com/watch?v=C834sFQvL1c&t=103s). This is not mandatory however for NTCS. 



## Summary of the steps

The end-to-end sequence of steps for participating in NTCS are as follows:

- Register for the study by completing the **[informed consent form](https://is.gd/neurotech_ch)**. 
- **Check your e-mail**. This will give you a personalized link for uploading your recorded data. It will also give you these instructions.  
- **Install miniconda**.  
- Set up your miniconda environment and **install eeg-notebooks**.  
- **Setup your eeg-device** (See specific instructions for [OpenBCI](), [Muse](), [Neurosity](), [Gtec]() devices).  
- **Run the experiment** using the script prompts  
- Locate the recorded data on your local machine and **run the data zipper command**   
- **Upload** your data to our secure servers via the personalized link from your first e-mail.  


## Full step-by-step instructions

### 1. Sign up and provide informed consent.
The consent form is located at this link: https://is.gd/neurotech_ch. You can open this link from your desktop computer, phone, tablet, or any other device. This form is to inform you about the overview of this project, how your data will be stored and shared, and possible outcomes aftethe study. You cannot take part in the study without filling out this form. You can fill out the consent form once and upload unlimited entries to the dataset. At the end, you will take a small quiz to ensure that you did not skip the information and actually read it though! It is necessary that you get all the questions correctly before moving forward with the study. If you cannot finish the quiz for any reason, we will be happy to reach out to you and resolve any issues! The form will guide you through that process if you cannot finish the quiz in any way. The procedure for filling out the form is described here: 

 1a. When you click on the link, you should be taken to a page like this, where you might be asked to verify being a human!

 1b. After pressing the “Begin Survey” button, you will be forwarded to a page describing some more privacy information, along with contact information you can use to reach out to the team.

 1c. In the next page, you can see the comprehensive information about the study, the data privacy and anonymity statements, contact information, possible benefits and risk statements for this study. You must read this section thoroughly, and will be quizzed on it in the next section.

 1d. After you proceed to the next section, you will see 8 multiple choice or yes/no questions testing your knowledge from the previous page. You must answer all these questions correctly to move forward with the study. At any point, you can go back to the last page by using the “<<< Previous page” button at the bottom of the screen to refresh your memory.

 1e. If you answer all of these questions correctly, you see this screen when you are once more asked if you have any unanswered questions, in which case the page will automatically forward you to a page where you can set up an appointment with us for a call.

 1f. After going forward to the next page, you will be forwarded to the signature page where you finalize your consent form. You will sign using your mouse, trackpad, or touch screen. It doesn’t need to be a beautiful signature, it just needs to be correct! After filling out the consent form and signing it, you will be sent an email including a unique link for you to upload your data.

### 2. Check your e-mail.
Check your inbox for the email address you provided in the consent form. This email includes instructions to run the experiment along with a unique link for you to upload your data. This email is unique to you. Please do not share it with anyone. You can use this link an infinite number of times to upload your data. Aside from the link, the rest of the instructions are the same for everyone and they are denoted below in this page for your reference as well.

When you click on the unique uploader link, you will be directed to a small form where you can upload your `.zip` file generated by eeg-notebooks securely to the CAMH servers. The data will be anonymized for further use and access. In this page, you will also answer a few anonymous questions regarding age, sex, and background neurological conditions. If you would like to upload another file, go back to your inbox and click on the link again, and rinse and repeat!
 
### 3. Install miniconda 
Miniconda makes it easy to manage multiple different Python installations on the same machine. While using miniconda environments is not required, we strongly recommend it. 

Get the latest version of minconda: https://docs.conda.io/en/latest/miniconda.html

Installation instructions: https://conda.io/projects/conda/en/latest/user-guide/install/index.html

### 4. Set up environment and install eeg-notebooks
Follow the instructions on this page of the eeg-notebooks docs
https://neurotechx.github.io/eeg-notebooks/getting_started/installation.html

```
conda create -n "ntcs" python=3.7 git pip wxpython

conda activate "ntcs"

git clone https://github.com/NeuroTechX/eeg-notebooks

cd eeg-notebooks

pip install -e .
```

### 5. Set up your EEG Device


#### 5.1 Windows+Muse device users: install BlueMuse software

#### 5.2 OpenBCI Devices

EEG Notebooks supports the OpenBCI Cyton (8 channel) and Ganglion (4 channel) boards. 
OpenBCI Getting Started Guides:
- Cyton: https://docs.openbci.com/GettingStarted/Boards/CytonGS/
- Ganglion: https://docs.openbci.com/GettingStarted/Boards/GanglionGS/

**Important** - Make sure to check that your FTDI driver is updates and configured properly:
https://docs.openbci.com/Troubleshooting/TroubleshootingLanding/

It's important to set up your electrodes so that they are mapped to the correct [10-20 locations](https://en.wikipedia.org/wiki/10%E2%80%9320_system_(EEG)#Higher-resolution_systems). See table below


|   | 8 Channel  | 4 Channel |
| :------------: | :------------: | :------------: |
| Ch 1  | FP1  | P7  |
| Ch 2  | FP2  | P8  |
| Ch 3  |  C3 | O1  |
| Ch 4  | C4  | O2  |
| Ch 5  | P7  | -  |
| Ch 6  | P8  | -  |
| Ch 7  | O1  | -  |
| Ch 8  | O2  | -  |
|Board| Cyton | Cyton or Ganglion|

OpenBCI Headset Guides:
- Ultracortex: 
https://docs.openbci.com/AddOns/Headwear/MarkIV/#electrode-location-overview
- Headband Kit: https://docs.openbci.com/AddOns/Headwear/HeadBand/
  - Note that the NTCS uses different electrode positions than the ones in this guide. You will need to adjust your setup so that the electrodes are on the back of the head

### 6. Run the visual N170 experiment

First, activate your conda environment

`conda activate ntcs`

Turn on your EEG device, and put it on your head. 


#### 6.1 Check your signal quality

Before starting data collection, you need to first verify that your readings have acceptable signal quality. 

`eeg-notebooks` has a simple command-line program for this purpose. Launch it with 

`eegnb checksigqual -ed mydevice`

(`ed` here stands for 'eeg device')

The signal quality checker performs a signal quality check every 5 seconds, and displays results on the command line. 

It will repeat this 10 times by default. If the signal is evaluated as good for all channels on the device for two runs in row, the program will automatically abort, and you are ready to move on to data collection. 

Once you launch the signal quality checker, you should do what you can to achieve good signal on all channels. First and foremost this means keeping still, breathing gently, and keeping eye movements and blinks to a minimum. 

After you have passed the initial signal quality check, you can move on to the experiment. 

You should repeat the signal quality checker a few times throughout the data collection - especially if you need to adjust the EEG position substantially for some reason. It is not necessary to re-run the signal quality check before all 10 recordings, however. 


#### 6.2 Run the experiment

Launch the run experiment "interactive prompt" with the command: 

`eegnb runexp -ip`

and follow the prompts for your specific hardware. When it asks which experiment to run, select "Visual N170"


##### 6.3.1 Get ready

The NTCS Phase 1 experiment is lasts approximately 1 hour.

When you are ready to begin proper data collection, you should ensure that you have sufficient time to complete (best to budget 1.5-2 hours), that you will not be interrupted during this time, and that you will be able to focus on the visual images presented on the screen with no distractions from your local environment. A small, quiet room such as an office or bedroom is ideal. 

##### Experiment details

The experiment consists of 10 short (5 minute) blocks, separated by short (~2 minute) rest periods. Each block consists of several hundred trials, each a few seconds long. On each trial a grayscale visual image or either a face or a house is quickly shown on the screen and then removed. The the visual system responds differentially to these type of visual stimuli, in ways that we know are measurable with EEG, and the time course of this differential response (sometimes called a 'difference wave') is what we are particularly interested in. 

After each block, there is a 2 minute rest. Use this time to take a breather and refresh your eyes and get ready for the next block. 



##### What to do

You are responsible for the timing of your rest periods and for initiating the next block on time after 2 minutes. 

To initiate a block, you will use the interactive command line prompt, where you should enter your device and subject information.

After the prompt questions are completed, the command line signal quality checker will be automatically launched. Take this opportunity if needed to adjust your device location on the head to maximize signal quality. 

The signal quality checker utility will cease when there are two successful 'good signal' evaluations, at which point you are good to go, and the visual images will begin to appear on screen. 





### 7. After recording, locate and zip your recorded data

#### 7.1 Take a look at what's there

When you have completed your recording session (or at any other time), you can check what data files you have recorded with eeg-notebooks using the following convenient command line utility:

`eegnb checkdirs`

This will print out to the command line a list of the folders and files present in the default storage location. This list includes two principal types: the demo data, and data you have recorded (`local' data). Note that any other data saved at non-default locations that you have specified yourself may not be included in this list. 

The default location is `~/.eegnb/data', file naming convention of `{experiment_name}_{site}-{day_month_year_hour:minute}'.csv - such as X.csv. 

#### 7.2 Compress your data

When you are ready to continue, run the file zipper command line utility. This will create a new file on your desktop. 


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



