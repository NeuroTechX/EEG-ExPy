
# Available Experiments

EEG-ExPy includes a number of EEG experiments for collecting data and evaluating BCI systems. The experiments are organized below by the neural/cognitive phenomena they target.

For instructions on how to run experiments, see the [Running Experiments](running_experiments.md) page.


## Visual ERP Experiments

### Visual P300

The P300 is a positive event-related potential (ERP) that occurs approximately 300ms after perceiving a novel or unexpected stimulus. It is most commonly elicited through 'oddball' paradigms, in which low-probability target items are interspersed with high-probability non-target items. Stimuli consist of images of cats and dogs, and participants are asked to count target images.

See the [Visual P300](../experiments/vp300) page for more details and notebook examples.

### Visual N170

The N170 is a large negative ERP component that occurs around 170ms after the perception of faces, but not objects or other body parts. It is most easily detected at lateral posterior electrodes. Stimuli consist of images of faces and houses, and the N170 is identified by comparing ERPs across the two stimulus categories.

See the [Visual N170](../experiments/vn170) page for more details and notebook examples.

### Visual Cueing

A spatial attention task in which a central cue indicates the likely location of an upcoming target. The task elicits reliable neural and cognitive effects including: enhanced ERPs for validly cued targets, faster response times, and lateralization of alpha-band oscillatory power after cue onset (alpha decreases contralateral to the cued side, and increases ipsilateral).

See the [Visual Cueing](../experiments/cueing) page for more details and notebook examples.

### Visual Go/No-Go

An experiment designed to measure the event-related potentials associated with executive control, inhibitory processing, and sustained attention. Participants are rapidly presented with a sequence of images and must press a key only for target images (Go trials), withholding responses for non-target images (No-Go trials).

See the [Visual Go/No-Go](../experiments/gonogo) page for more details and notebook examples.


## Visual Frequency-Tagging Experiments

### Visual SSVEP

The steady-state visual evoked potential (SSVEP) is a repetitive neural response produced when viewing a flickering stimulus. Electrical activity at the same frequency as the visual stimulation can be detected in occipital areas of the brain. The SSVEP is widely used in BCI applications due to its ease of detection and high frequency resolution.

See the [Visual SSVEP](../experiments/vssvep) page for more details and notebook examples.


## Auditory Experiments

### Auditory Oddball (P300)

An auditory variant of the P300 oddball paradigm. Participants listen to sequences of tones in which infrequent 'oddball' tones are embedded among frequent standard tones. The auditory P300 is elicited by the infrequent tones and is detectable at temporal and parietal electrodes. Two variants are available: the original auditory oddball and the Diaconescu variant.

### Auditory SSAEP

The steady-state auditory evoked potential (SSAEP) — also known as the auditory steady-state response (ASSR) — is a frequency-domain neural response to amplitude-modulated tones. Modulation frequencies of 40 Hz and 45 Hz applied to carrier frequencies of 900 Hz and 770 Hz respectively produce clear peaks in the EEG power spectrum at the modulation frequencies. Two variants are available: the original dual-frequency version and a single-frequency version.


## Resting State

### Resting State (Eyes Open / Eyes Closed)

A baseline resting-state recording in which participants alternate between blocks of eyes-open and eyes-closed rest. This paradigm is useful for measuring spontaneous neural activity, particularly alpha-band oscillations (8–12 Hz), which are known to increase when the eyes are closed. Auditory and visual cues guide transitions between blocks.


## Other Experiments

### Visual Code vs. Prose

An experiment investigating whether EEG can distinguish between reading computer code and reading natural language prose. Based on prior fMRI and EEG replication studies, participants read short passages of code and prose while neural activity is recorded.


## Older / Unvalidated Experiments

The following experiments were explored in earlier versions of the library or have not yet been fully validated. They are retained here for reference.

### C1 and P1

C1 and P1 are two ERPs related to the early visual processing of a stimulus. The C1 is the first component, appearing in the 65–90 ms range after stimulus onset, while the P1 appears later, around 100 ms. A left/right visual field paradigm can reveal contralateral patterns of C1 and P1 in temporal and anterior electrodes.

### Auditory P300

An auditory stimulus variant of the P300. Auditory P300s are typically less prominent than visual P300s, but may be better suited to headsets with temporal electrode placement, such as the Muse, given its proximity to auditory cortex.

### N100–P200

The combination of a negative evoked potential around 100 ms and a positive potential around 200 ms following any unpredictable stimulus onset. These components have been observed in earlier SSAEP experiments but have not been independently classified or tested in this library.

### On-task Beta

Increased beta-band (13–30 Hz) activity observed during active cognitive task performance. Noticed in earlier visual grating experiments but difficult to reliably extract with low-density EEG.

### Alpha Reset

A transient increase in alpha activity following the end of a visual stimulus, observed in earlier visual grating experiments.
