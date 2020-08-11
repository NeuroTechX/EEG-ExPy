# Running eeg-notebooks on Linux

There were some issues using Linux with the notebooks. ./notebooks/utils/utils.py was edited and ./notebooks/linux_muse was added to get around the issues.

Then two notebooks (SSVEP and Raw_EEG) were ported over to versions that work with Linux+Python3. Tested system was an Asus Zenbook 13 running Ubuntu 18 LTS.

## Setup

```
sudo apt-get update
python3 -m virtualenv venv
source venv/bin/activae
pip3 install -r requirements.txt
pip3 install pygatt==3.1.1
pip3 install bluepy
pip3 install pygame #not sure why this isn't needed/included in the other requirement.txt?
sudo apt-get install libpcap-dev #for muselsl
```

### Bluepy setup

*Modify the path to match the path of your Python virtualenv*

```
sudo setcap 'cap_net_raw,cap_net_admin+eip' ~/Tester/blueberry/eeg-notebooks/venv/lib/python3.6/site-packages/bluepy/bluepy-helper
```
