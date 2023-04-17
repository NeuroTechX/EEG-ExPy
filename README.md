# Welcome to the modified eeg-notebooks

## Installation

```
conda create -y -n eeg_experiments python=3.7 wxpython
conda activate eeg_experiments
```
clone the modified package and install:
```
git clone https://github.com/xuetengcode/eeg-notebooks.git
cd <to eeg-nootbooks folder>
pip install -e .
```

Then, turn on your device and run the modified N170 (house vs. landscape):
```
eegnb runexp -ip
```
