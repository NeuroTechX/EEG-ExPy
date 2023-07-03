# Welcome to the modified eeg-notebooks
## Run from University Computers
```
cd eeg-notebook
git pull
```

## Installation on personal computers

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

## Creat a symbolic link to the collected data

If you want to check the csv files, run the bash script, `link_data.sh`, at eeg-notebook folder. It will create a symbolic link from the hidden data folder to `~/eegnb`