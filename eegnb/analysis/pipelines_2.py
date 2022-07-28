

"""

Want functionality of the following form, 

epoch_kwargs = dict(tmin=-0.1, tmax=0.6, baseline=None,
                    reject={'eeg': 5e-5}, preload=True, 
                    verbose=False, picks=[0,1,2,3],
                    event_id = OrderedDict(House=1,Face=2) )
raw,erp = compute_erp(fnames,epoch_kwargs)
plot_kwargs = dict(conditions = epoch_kwargs['event_id'],
                   ci=97.5, n_boot=1000, title='',
                   diff_waveform=None, #(1, 2))
                   channel_order=[1,0,2,3]))
make_erp_plot(epochs,plot_kwargs)

"""

# Kwargs accepts in the form of a dict 
# Args accepts in the form of tuple

import os 
from collections import OrderedDict
import warnings
import matplotlib.pyplot as plt


def compute_erp(fnames, **epoch_kwargs):
    """
    Function to retrive the raw data and compute the Event Related Potential

    Procedure
    1. Loads the data using file names and retrives if not already present
    2. Epochs the data
    3. Computes the ERP
    4. Returns the raw and ERP objects
    
    Usage:
    epoch_kwargs = dict(experiment = 'visual-N170', tmin=-0.1, tmax=0.6, baseline=None,
                    reject={'eeg': 5e-5}, preload=True, 
                    verbose=False, picks=[0,1,2,3],
                    event_id = OrderedDict(House=1,Face=2) )
    raw,erp = compute_erp(fnames,epoch_kwargs)
    """

    # Load the data

    # If dataset hasn't been downloaded yet, download it
    if not os.path.isdir(fnames):
        fetch_dataset(data_dir=fnames, experiment=experiment, site='eegnb_examples');

        raw = load_data(subject,session,
                        experiment=experiment, site='eegnb_examples', device_name='muse2016_bfn',
                        data_dir = eegnb_data_path)
    
    # Otherwise simply load the data
    else:
        raw = load_csv_as_raw(fnames,**epoch_kwargs)        
    
    subject = 1
    session = 1

    # Epochs the data
    epochs = Epochs(raw, **epoch_kwargs)
    
    # Don't know if we want to include this 
    print('sample drop %: ', (1 - len(epochs.events)/len(events)) * 100)
    print(epochs)

    # Compute the ERP
    erp = epochs.average()

    return raw,erp 
    
def make_erp_plot(epochs, **plot_kwargs):
    """
    Function to make the ERP plot
    
    Procedure
    
    Usage:
    plot_kwargs = dict(conditions = epoch_kwargs['event_id'],
                   ci=97.5, n_boot=1000, title='',
                   diff_waveform=None, #(1, 2))
                   channel_order=[1,0,2,3]))
    make_erp_plot(epochs,plot_kwargs)
    """

    fig, ax = plot_conditions(epochs, **plot_kwargs)

    # Manually adjust the ylims
    for i in [0,2]: ax[i].set_ylim([-0.5,0.5])
    for i in [1,3]: ax[i].set_ylim([-1.5,2.5])


    # Make Plots
    raw.plot_psd(fmin=1, fmax=30)
    plt.show()
    
    return