"""
Introduction to EEG decoding and Riemannian geometry
====================================================

In this tutorial, we provide a hands-on introduction to the different EEG
decoding algorithms used in `eeg-notebooks`.

What is EEG decoding?
---------------------

The task of EEG decoding consists in using EEG-derived features to predict an
experimental property, e.g., using a subject's EEG to predict whether they were
seeing the picture of a human face or of a house [1]_
[2]_. This is in contrast to encoding models, in which
experimental properties are used to predict what the neural activity looked
like at the time of stimulus presentation. Decoding tasks are frequently found
in brain-computer interfacing (BCI) research, where the goal is to decode the
user's intent using their neural data.

Structure of this notebook
--------------------------

We start by presenting the main decoding algorithms used in `eeg-notebooks`:
vectorization and logistic regression, Riemannian geometry-based decoding and
[something else?]. We focus on explaining the basic principles behind these
approaches. Next, we compare these decoding approaches on data pre-recorded
with `eeg-notebooks`: ERP, SSVEP and [motor imagery/something else?] data. We
conclude with a quick recap and provide key references to further your
understanding of EEG decoding algorithms.

.. contents::
   :local:
   :depth: 2

:Authors:
    Hubert Banville <hubert.jbanville@gmail.com>;
    Jadin Tredup <>

:License: BSD (3-clause)

"""


###############################################################################
# Setup
# ---------------------

# General imports
import numpy as np
import mne
from mne import Epochs, find_events
import matplotlib.pyplot as plt

from eegnb.datasets.datasets import fetch_dataset
from eegnb.analysis.utils import load_data


mne.set_log_level('ERROR')  # To avoid flooding the cell outputs with messages
random_state = 87


###############################################################################
# A. Presentation of decoding algorithms
# --------------------------------------
#
# In this section, we gradually introduce the decoding algorithms used in
# `eeg-notebooks`. We provide some general background on machine learning
# classification tasks, and briefly show code to run these algorithms. More
# extensive comparisons done with cross-validation, however, will be done in
# the Section B.
#

###############################################################################
# 0. Some prerequisites
# ~~~~~~~~~~~~~~~~~~~~~
#
# We start by introducing some important concepts for understanding this
# section of the tutorial.
#
# We have pre-recorded data using different paradigms available in the
# `eeg-notebooks` library. For instance, let's look at the data recorded with
# the N170 paradigm.
#

# download data
fetch_dataset(experiment='visual-N170')

# load from storage
raw = load_data(subject_id='all', session_nb='all', device_name='muse2016',
                experiment='visual-N170', site='eegnb_examples')

# create an array with timestamps and type of stimuli (i.e., face or house)
events = find_events(raw)
event_id = {'House': 1, 'Face': 2}

# create MNE Epochs object with epochs around stimulus presentation
epochs = Epochs(
    raw, events=events, event_id=event_id, tmin=-0.1, tmax=0.8, baseline=None,
    reject={'eeg': 75e-6}, preload=True, verbose=False, picks=[0,1,2,3]
)

data = epochs.get_data()
print(f'Loaded data has shape: {data.shape}')

###############################################################################
# The data has shape (:math:`N`, :math:`C`, :math:`T`), where
#
# * :math:`N`: number of trials, i.e., number of EEG windows that were recorded
#   (e.g., 2292 in our N170 dataset)
# * :math:`C`: number of EEG channels (e.g., 4 if using Muse)
# * :math:`T`: number of EEG time points in a window (e.g., 232 in our N170 dataset)
#
# Additionally, we have a label vector `y` that tells us what class each one of
# our :math:`N` examples are from. For instance, with the N170 task, we have classes
# 1 and 2, corresponding to 'house' and 'face' (i.e., the subject saw a picture
# of a house or a picture of a face).
#

y = epochs.events[:, -1]

print(f'Number of "house" events: {sum(y == 1)}')
print(f'Number of "face" events: {sum(y == 2)}')

###############################################################################
# Our decoding task consists in training a machine learning classifier to
# predict, given an EEG window :math:`X_t` (of shape :math:`C \times T`), which class it is
# from. To do so, we will split our data into a *training* and a *test* set.
#
# The **training set** will be used to train the classifier. The **test set**,
# on the other hand, will be used to assess how well our classifier works on
# data it has never seen. A straightforward way to do this is to use 80% of our
# :math:`N` examples for training, and keep the remaining 20% for testing.
#

# Example of split into training and test sets
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    data, y, test_size=0.2, random_state=87)

print(f'Number of examples in training set: {X_train.shape[0]}')
print(f'Number of examples in test set: {X_test.shape[0]}')


###############################################################################
# To further improve our estimation of classification performance, we can
# repeat this train/test split multiple times (for example, we will use 5-fold
# cross-validation below [3]).
#
# We are now ready to look into the different decoding approaches!
#


###############################################################################
# 1. A simple approach: vectorization and logistic regression
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# One of the simplest approaches to event-related EEG classification consists
# in vectorizing the data followed by linear classification.
#
# This approach consists in feeding the flattened EEG windows to a classifier
# such as logistic regression. Starting with our :math:`N` EEG windows of shape
# :math:`(C, T)`, we first vectorize (i.e., flatten) the windows to be of shape
# :math:`D = C \times T`.
#

# Example of how to vectorize
print(f'Shape of training set before vectorization: {X_train.shape}')
vect_X_train = X_train.reshape(X_train.shape[0], -1)
vect_X_test = X_test.reshape(X_test.shape[0], -1)
print(f'Shape of training set after vectorization: {vect_X_train.shape}')


###############################################################################
# Next, we scale the data so that each dimension of the input has a mean of 0
# and a standard deviation of 1. This will help our classifier converge more
# easily. Importantly, this step is done using the training set as reference.
#

# Example standardization step
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
scaled_X_train = scaler.fit_transform(vect_X_train)
scaled_X_test = scaler.transform(vect_X_test)

print(f'Average feature-wise mean: {scaled_X_train.mean():0.5f}')
print('Average feature-wise standard deviation: '
      f'{scaled_X_train.std(axis=0).mean():0.5f}')

###############################################################################
# Finally, we use the normalized examples to train a linear logistic regression
# classifier.
#

from sklearn.linear_model import LogisticRegression

log_reg = LogisticRegression(random_state=87).fit(scaled_X_train, y_train)
test_acc = log_reg.score(scaled_X_test, y_test)

print(f'\nAccuracy of vect + log reg: {test_acc * 100:0.2f}%\n')


###############################################################################
# This simple method works barely above chance-level here, but it can work
# surprisingly well in some cases. In any case, we can do potentially much
# better by explicitly taking into account the spatial structure of the EEG
# data, as we will see in the next section.
#


###############################################################################
# 2. State-of-the-art decoding with Riemannian geometry
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# EEG decoding approaches based on **Riemannian geometry** (RG) have led to
# state-of-the-art performance on many types of EEG decoding tasks. The basic
# idea behind this approach is to leverage the spatial structure of the EEG,
# i.e., the fact that there are multiple channels which co-vary in specific
# ways, to improve classification performance [3]_. To understand RG approaches,
# we must first take a look at covariance matrices.
#
# .. note::
#
#   **tl;wr** : A good way to summarize EEG windows is with their *covariance matrices*.
#   However, if we want to train classifiers on covariance matrices we need to
#   take into account their specific geometry. That's why we use Riemannian
#   geometry metrics, which are the right metrics for covariance matrices - and
#   that comes with a bunch of nice properties such as invariance under linear
#   transformations.
#

###############################################################################
# Covariance matrices
# ```````````````````
#
# Covariance matrices are square matrices that describe how different random
# variables are related. For instance, going back to our dataset of EEG windows
# with :math:`C=4` channels, the covariance matrix :math:`\Sigma` looks like this:
#
# .. image:: /img/cov_mat.png
#
# Each cell in that matrix tells us how much each pair of channels **co-vary**,
# i.e., how related the two channels are. This is great for classifying EEG
# windows: we expect the way channels co-vary to be specific to each class
# (e.g., when someone looks at a face vs. at a house, the different channels
# should react differently).
#
# The formula to compute K is as follows:
#
# .. math::
#
#   \Sigma_t = \frac{X_t X_t^\top}{T-1}
#
# We have to make sure the channels have a mean of zero first, which can be
# done with highpass filtering, or by doing window-wise normalization.
#
# .. note::
#
#   This is what is called the **sample covariance matrix**. There exists more
#   robust ways of computing :math:`\Sigma` that we won't cover here [3]_.
#
# As seen in the first illustration above, the diagonal of :math:`\Sigma` contains
# the **variance** of the signals, which you might already be familiar with.
#
# Let's compute the sample covariances for the windows in our dataset:

# Computing covariance matrices
norm_X_train = X_train - X_train.mean(axis=-1, keepdims=True)  # Remove DC offset
norm_X_train *= 1e6  # Convert from V to uV

covs_train = (norm_X_train @ norm_X_train.transpose(0, 2, 1)) / (
    norm_X_train.shape[-1] - 1)
print(f'Training set covariances have shape: {covs_train.shape}')

# Visualizing a covariance matrix
ind = 1600
ch_names = [f'ch{i}' for i in range(1, 5)]
max_ampl = np.abs(covs_train[ind]).max()  # find max abs(value) for plotting

fig, ax = plt.subplots()
im = ax.imshow(covs_train[ind], cmap='bwr', vmin=-max_ampl, vmax=max_ampl)
ax.set_yticks(range(4))
ax.set_yticklabels(ch_names)
ax.set_xticks(range(4))
ax.set_xticklabels(ch_names)
fig.colorbar(im, ax=ax, fraction=0.05)
ax.set_title('A covariance matrix\nin our dataset')
fig.tight_layout()


###############################################################################
# Now that we have these covariance matrices, how do we use them for
# **predicting which class an example comes from**?
#
# A simple approach is to compare the covariance matrix of that window to the
# average covariance matrix for each class :math:`\Sigma_{class~k}` - whichever one
# has the smallest distance is then used as label prediction. This approach is
# called "Minimum Distance to the Mean" (MDM), and works very well in practice.
#
# One issue arises here though: **how should we measure this distance**? A
# naive approach would be to use the Euclidean distance:
#
# TODO: Change sigma to K so we can use sums?
#
# .. math::
#
#   \left| \Sigma_t - \hat\Sigma_{class 1}\right|
#

# Computing Euclidean distance between an example and class 1's mean covariance
class1_cov = covs_train[y_train == 1].mean(axis=0)
eucl_dist = np.sum(np.abs(covs_train[0] - class1_cov))

print(f'Euclidean distance between an example and class 1: {eucl_dist:0.2f}')


###############################################################################
# However, this does not respect the structure of covariance matrices. Indeed,
# covariance matrices are **positive definitive matrices**, meaning they have
# some specific properties such as positive values on their diagonal (and
# positive eigenvalues). To respect their structure, we need to use the
# Riemannian geometric distance metric :math:`\delta_G`:
#
# .. math::
#
#   \delta_G(\Sigma_t , \Sigma_{class~i}) = \left\lVert \log \Sigma_t^{-\frac{1}{2}} \Sigma_{class~i} \Sigma_t^{-\frac{1}{2}} \right\lVert_F = \sqrt{\sum_{n=1}^N \log^2 \lambda_n}
#
# (If you are interested in the details, a detailed explanation can be found
# in [3]_.) This might overall look complicated, but existing implementations
# such as those in [pyriemann]_ take care of computing this distance for us.
# For instance:
#

# Computing the geometric distance between an example and class 1's average covariance
from pyriemann.utils.distance import distance_riemann

distance_riemann(covs_train[0], class1_cov)
print(f'Geometric distance between an example and class 1: {eucl_dist:0.2f}')


###############################################################################
# These absolute distance values might not be very informative for now, but
# once we include entire training sets below they will make more sense.
#
# Equipped with **covariance matrices** and this **geometric distance metric**,
# we can now train our first Riemannian geometry-based decoding pipelines,
# which we'll do in the next section.
#
# Before moving on though, what if we want to leverage more complicated
# classification approaches than the relatively simple MDM, e.g., logistic
# regression or support vector machines (SVMs)? To do this, we need to
# introduce the concept of **tangent space** (TS). Briefly put, the tangent
# space is a hyperplane onto which we will project the covariance matrices.
# Once projected into this tangent space, our covariance matrices can now be
# compared reasonably well using a standard Euclidean distance metric. The
# standard visual explanation for this looks like this (taken from [3]_):
#
# .. image:: /img/riemann_tangent_space.png
#
# Again, [pyriemann]_ takes care of that step for us.
#
# Using RG approaches comes with **useful properties**. For instance, the
# geometric distance metric is invariant to linear transformations of the data.
# This means we don't need to apply spatial filtering steps used in traditional
# pipelines (PCA, ICA, CSP, etc.) - we are effectively already working in
# source space! RG approaches are also more robust to outliers and facilitate
# generalization across subjects and recording sessions.
#


###############################################################################
# 3. Other approaches
# ~~~~~~~~~~~~~~~~~~~
#
# TODO: introduce FBCSP, XDawn, deep learning, etc.
#

###############################################################################
# B. Application to `eeg-notebooks` data
# --------------------------------------
#
# In this section, we compare the decoding approaches introduced above on data
# collected with `eeg-notebooks`.
#
# We start by loading the different datasets available by default in
# `eeg-notebooks` on top of the N170 we already loaded above: P300 and SSVEP.
# Then, for each dataset, we compare different approaches and report
# performance.
#


###############################################################################
# 1. Loading data
# ~~~~~~~~~~~~~~~
#

# download ERP data
fetch_dataset(experiment='visual-N170')
# download SSVEP data
fetch_dataset(experiment='visual-SSVEP', site='jadinlab_home', device='cyton')


###############################################################################
# 2. Event-related potential (ERP) data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# We load the N170 data from above again:
#

# Download data
fetch_dataset(experiment='visual-N170')

# Load from storage
raw = load_data(subject_id='all', session_nb='all', device_name='muse2016',
                experiment='visual-N170', site='eegnb_examples')
raw.filter(1, 30, method='iir')

# Create an array containing timestamps and stimulus type (i.e. face or house)
events = find_events(raw)
event_id ={'House': 1, 'Face': 2}

# Create an MNE Epochs object representing all the epochs around stimulus presentation
epochs = Epochs(
    raw, events=events, event_id=event_id, tmin=-0.1, tmax=0.8, baseline=None,
    reject={'eeg': 75e-6}, preload=True, verbose=False, picks=[0,1,2,3]
)

data = epochs.get_data()

# Format data
epochs.pick_types(eeg=True)
X = epochs.get_data() * 1e6
times = epochs.times
y = epochs.events[:, -1]

# Split into training and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42)


###############################################################################
# Preprocessing - ERP temporal prototypes
# ````````````````````````````````````````
#
# The first step of preprocessing ERP data for Riemmanian Geometry classifiers
# involves creating temporal prototypes of each ERP class. To do this, we
# collect every instance of each ERP from the training set and average them. In
# the case of the N170 experiment, we are classifying two classes: one for the
# N170 and another for a non-ERP class. Thus, we only need to create one
# prototype.
#
# .. math::
#
#   \bar{X}_{(1)} = \bar{X}_{(N170)}
#

target_idx = np.where(y_train == 2)
X_erp = X_train[target_idx]

prototype = X_erp.mean(axis=0)


###############################################################################
# Preprocessing - Construct the super-trial
# ``````````````````````````````````````````
# .. math::
#
#   X^{ERP}_Z = \begin{pmatrix} \bar{X}_{(1)} \\ \cdots \\ \bar{X}_{(Z)} \\ X_Z \end{pmatrix} \in \mathcal{R}^{N(Z+1)xT}
#

# get single trial
trial = X_test[0]

# add to temporal prototype
super_trial = np.vstack((prototype, trial))
super_trial.shape

###############################################################################
# Processing - Estimate the covariance matrix
# ````````````````````````````````````````````
# .. math::
#
#   C_Z = \frac{1}{T-1} \left( X^{ERP}_Z \left( X^{ERP}_Z \right)^T \right) = \frac{1}{T-1} \begin{pmatrix}
#   \bar{X}_.\bar{X}^T_. & \left( X_Z \bar{X}_. \right)^T \\
#   X_Z \bar{X}_.^T & X_Z X_Z^T
#   \end{pmatrix}  \in \mathcal{R}^{N(Z+1)\times N(Z+1)}
#


###############################################################################
# Using pyriemann
# ```````````````
#

from pyriemann.estimation import ERPCovariances

# Define covariance estimator with temporal prototypes
covariance_estimator = ERPCovariances().fit(X_train, y_train)

# estimate the covariance matrices of the test set
X_cov_est = covariance_estimator.transform(X_test)


###############################################################################
# 3. Steady-state visually evoked potentials (SSVEP)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#

# load data
raw = load_data(subject_id='all', session_nb='all', device_name='cyton',
                experiment='visual-SSVEP', site='jadinlab_home')


###############################################################################
# Preprocessing data - Creating super trials
# ```````````````````````````````````````````
#
# The first step to using RG for decoding and classifying SSVEP data is to
# create a super trial, :math:`X^{SSVEP}_z` which is of shape :math:`NF \times T` where
# :math:`N` is the number of electrodes used, :math:`F` is the number of frequencies
# to decode, and :math:`T` is the number of time points.
#
# .. math::
#
#   X^{SSVEP}_z = \begin{pmatrix} X_{(1)} \\ \cdots \\ X_{(F)} \end{pmatrix} \in \mathcal{R}^{NF\times T}
#
#
# To create the super trials we will bandpass the original data at both 20hz
# and 30hz to isolate the desired frequencies. The resulting signals are then
# concatenated to create a "Supertrial" for the whole recording. After this
# step, the data needs to be seperated into epochs based on the stimulus onset.
#

# Bandpass filter raw data
raw_filt_20 = raw.copy().filter(15, 25, method='iir')
raw_filt_30 = raw.copy().filter(25, 35, method='iir')

raw_filt_30.rename_channels(lambda x: x + '_30Hz')
raw_filt_20.rename_channels(lambda x: x + '_20Hz')

# Concatenate with the bandpass filtered channels to create one super trial
# containing every epoch
raw_all = raw_filt_30.add_channels(
    [raw_filt_20],
    force_update_info=True
)

# Extract epochs to create individual super trials
events = find_events(raw_all)
event_id = {'30 Hz': 1, '20 Hz': 2}

epochs_all = Epochs(
    raw_all, events=events, event_id=event_id,
    tmin=1, tmax=3, baseline=None,
    reject={'eeg': 100e-6}, preload=True, verbose=False,
)

epochs_all.pick_types(eeg=True)

# Decompose into data and labels
X = epochs_all.get_data() * 1e6
y = epochs_all.events[:, -1]


###############################################################################
# Preprocessing - Estimating the covariance matrix
# `````````````````````````````````````````````````
#
# The next step in the process is to estimate the covariance matrix for each
# super trial using the equation:
#
# .. math::
#
#   C_Z=\frac{1}{T-1}\left[ X^{SSVEP}_Z \left( X^{SSVEP}_Z \right)^T \right] = \frac{1}{T-1}
#   \begin{pmatrix}
#   X_{(1)}X^T_{(1)} & \cdots & X_{(1)}X^T_{(F)} \\
#   \vdots & \ddots & \vdots \\
#   X_{(F)}X^T_{(1)} & \cdots & X_{(F)}X^T_{(F)} \\
#   \end{pmatrix}
#   \in \mathcal{R}^{NF\times NF}
#

sup_trial = X[0]
n_samples = sup_trial.shape[1]
cov_est = (1/(n_samples-1))*np.matmul(sup_trial, sup_trial.T)


###############################################################################
# Using PyRiemann
# ```````````````
#
# The same covariance matrix can be calculated for all epochs at once using
# the `PyRiemann.Estimation.Covariances` class.
#

# get covariance matrices
cov_data = Covariances().transform(X)


###############################################################################
# Conclusion
# ----------
#
# In this tutorial, we introduced different EEG decoding approaches used in
# `eeg-notebooks`. We applied them to pre-recorded data available with
# `eeg-notebooks`.
#

###############################################################################
# Going further
# -------------
#
# Software
# ~~~~~~~~
#
# .. [pyriemann] `pyriemann <https://github.com/alexandrebarachant/pyRiemann>`_: a
#     Python library that implements most tools required to leverage Riemannian
#     geometry on EEG data.
#
# References
# ~~~~~~~~~~
#
# .. [1] Holdgraf, C. R., Rieger, J. W., Micheli, C., Martin,
#     S., Knight, R. T., & Theunissen, F. E. (2017). Encoding and decoding models
#     in cognitive electrophysiology. Frontiers in systems neuroscience, 11, 61.
# .. [2] King, J. R., Gwilliams, L., Holdgraf, C., Sassenhagen,
#     J., Barachant, A., Engemann, D., ... & Gramfort, A. (2018). Encoding and
#     decoding neuronal dynamics: Methodological framework to uncover the
#     algorithms of cognition.
# .. [3] Congedo, M., Barachant, A., & Bhatia, R. (2017).
#     Riemannian geometry for EEG-based brain-computer interfaces; a primer and a
#     review. Brain-Computer Interfaces, 4(3), 155-174.
#
