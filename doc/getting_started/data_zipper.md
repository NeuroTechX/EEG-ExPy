# Data Zipping
After you have ran experiments, you can compress all recorded data as a zip folder. The method for doing this is using the command line tool with the flags detailed below. 

**Command Line Interface**

To activate the command line tool, open a command/terminal prompt and enter `eegnb runzip` followed by the appropriate flag for your desired experiment. Command line tool looks through folders in `~/.eegnb/data` for compression. Zip files will be outputted in the format of ~/Desktop with the following filename {experiment_name}_{site}-{day_month_year}{hour:minute}_zipped
The possible flags are

* *-ex ; --experiment*: The experiment to be run
* *-s ; --site*: Subfolder within the experiment
* *-ip ; --prompt*: Bypass the other flags to activate an interactive prompt

**Using the introprompt flag**

If using the -ip flag the user will be prompted to input the various session parameters. The prompts are detailed below.

***Experiment Selection***
```
Please select which experiment you would like to run: 
[0] Visual N170
[1] Visual P300
[2] Visual SSVEP
[3] visual-cue (no description)
[4] visual-codeprose (no description)
[5] Auditory SSAEP (orig)
[6] Auditory SSAEP (single freq)
[7] Auditory oddball (orig)
[8] Auditory oddball (diaconescu)

Enter Experiment Selection:
```
This section allows you to select one of the above experiments to run. There are other experiments available, however, they have not yet been updated for the new API to be device agnostic. As they get updated, more experiments will populate this section.

***Site Selection***
```
Please select which experiment subfolder you would like to zip. Default 'local_ntcs'

Current subfolders for experiment visual-N170:

['local','local_ntcs','temp']

Enter folder:
```

This selection allows you to select the subfolder for the experiment you have previously chosen. The example provided was for example sites in the visual-N170 folder.

