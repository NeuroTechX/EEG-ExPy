# -*- coding: utf-8 -*-
"""
Clustering Methods Comparison of N170 ERP EEG Data

We can explore machine learning methods of classification and clustering of the N170 EEG data.
"""

from collections import OrderedDict

from eegnb.analysis.utils import load_data, plot_conditions
from eegnb.datasets import fetch_dataset

from functools import partial

from itertools import cycle, islice

from matplotlib import pyplot as plt
from matplotlib.ticker import NullFormatter

from mne import Epochs, find_events
from mne.decoding import Vectorizer
from mpl_toolkits.mplot3d import Axes3D

import numpy as np
import os

from pyriemann.classification import MDM
from pyriemann.embedding import Embedding
from pyriemann.estimation import XdawnCovariances
from pyriemann.tangentspace import TangentSpace
from pyriemann.utils.viz import plot_confusion_matrix

import seaborn as sns
from sklearn import cluster, mixture
from sklearn.manifold import LocallyLinearEmbedding, Isomap, MDS, SpectralEmbedding, TSNE
from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import StandardScaler

from pyriemann.classification import MDM

from time import time

import warnings
warnings.filterwarnings('ignore')

"""Load the data."""

eegnb_data_path = os.path.join(os.path.expanduser('~/'),'.eegnb', 'data')
n170_data_path = os.path.join(eegnb_data_path, 'visual-N170', 'eegnb_examples')

# If dataset hasn't been downloaded yet, download it
if not os.path.isdir(n170_data_path):
    fetch_dataset(data_dir=eegnb_data_path, experiment='visual-N170', site='eegnb_examples');

subject = 1
session = 1
n170raw = load_data(subject,session,
                    experiment='visual-N170', site='eegnb_examples', device_name='muse2016',
                    data_dir = eegnb_data_path)

"""Filter the data."""

n170raw.filter(1,30, method='iir')

"""Visualize."""

n170raw.plot_psd(fmin=1, fmax=30);

"""Perform the epoching."""

# Create an array containing the timestamps and type of each event/stimulus.
n170events = find_events(n170raw)
n170event_id = {'House': 1, 'Face': 2}

# Create an MNE Epochs object representing all the epochs around stimulus presentation
n170epochs = Epochs(n170raw, events=n170events, event_id=n170event_id,
                tmin=-0.1, tmax=0.8, baseline=None,
                reject={'eeg': 75e-6}, preload=True,
                verbose=False, picks=[0,1,2,3])
n170epochs
print('sample drop %: ', (1 - len(n170epochs.events)/len(n170events)) * 100)

# Get data from Epochs
n170X = n170epochs.get_data()
n170y = n170epochs.events[:, -1]

n170conditions = OrderedDict()
n170conditions['House'] = [1]
n170conditions['Face'] = [2]

fig, ax = plot_conditions(n170epochs, conditions=n170conditions,
                          ci=97.5, n_boot=1000, title='Clustering algorithms for N170 data',
                          diff_waveform=(1, 2))

"""
Compare different methods of clustering
"""

plt.figure(figsize=(9 * 2 + 3, 12.5))
plt.subplots_adjust(left=.02, right=.98, bottom=.001, top=.96, wspace=.05,
                    hspace=.01)

plot_num = 1

default_base = {'quantile': .3,
                'eps': .3,
                'damping': .9,
                'preference': -200,
                'n_neighbors': 281,
                'n_clusters': 2,
                'min_samples': 20,
                'xi': 0.05,
                'min_cluster_size': 0.1}

n170 = [n170X, n170y]

datasets = [
    (n170, {'damping': .77, 'preference': -240,
                     'quantile': .2, 'n_clusters': 2,
                     'min_samples': 20, 'xi': 0.25})]

for i_dataset, (dataset, algo_params) in enumerate(datasets):
    # Update the parameters with dataset-specific values.
    params = default_base.copy()
    params.update(algo_params)
    X, y = dataset

    # Reshape the input data to two dimensions.
    nsamples, nx, ny = X.shape
    d2X = X.reshape((nsamples,nx*ny))

    # Normalize the dataset for easier parameter selection.
    X = StandardScaler().fit_transform(d2X)

    # Estimate bandwidth for mean shift.
    bandwidth = cluster.estimate_bandwidth(X, quantile=params['quantile'])

    # Create the connectivity matrix for structured Ward.
    connectivity = kneighbors_graph(
        X, n_neighbors=params['n_neighbors'], include_self=False)
    # Calculate the connectivity symmetric.
    connectivity = 0.5 * (connectivity + connectivity.T)

    # Create cluster objects.
    ms = cluster.MeanShift(bandwidth=bandwidth, bin_seeding=True)
    two_means = cluster.MiniBatchKMeans(n_clusters=params['n_clusters'])
    ward = cluster.AgglomerativeClustering(
        n_clusters=params['n_clusters'], linkage='ward',
        connectivity=connectivity)
    spectral = cluster.SpectralClustering(
        n_clusters=params['n_clusters'], eigen_solver='arpack',
        affinity="nearest_neighbors")
    dbscan = cluster.DBSCAN(eps=params['eps'])
    optics = cluster.OPTICS(min_samples=params['min_samples'],
                            xi=params['xi'],
                            min_cluster_size=params['min_cluster_size'])
    affinity_propagation = cluster.AffinityPropagation(
        damping=params['damping'], preference=params['preference'])
    average_linkage = cluster.AgglomerativeClustering(
        linkage="average", affinity="cityblock",
        n_clusters=params['n_clusters'], connectivity=connectivity)
    birch = cluster.Birch(n_clusters=params['n_clusters'])
    gmm = mixture.GaussianMixture(
        n_components=params['n_clusters'], covariance_type='full')

    clustering_algorithms = (
        ('MiniBatchKMeans', two_means),
        ('AffinityPropagation', affinity_propagation),
        ('MeanShift', ms),
        ('SpectralClustering', spectral),
        ('Ward', ward),
        # ('AgglomerativeClustering', average_linkage),
        # ('DBSCAN', dbscan),
        # ('OPTICS', optics),
        # ('Birch', birch),
        # ('GaussianMixture', gmm)
    )

    for name, algorithm in clustering_algorithms:
        t0 = time()

        # Catch warnings related to kneighbors_graph.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="the number of connected components of the " +
                "connectivity matrix is [0-9]{1,2}" +
                " > 1. Completing it to avoid stopping the tree early.",
                category=UserWarning)
            warnings.filterwarnings(
                "ignore",
                message="Graph is not fully connected, spectral embedding" +
                " may not work as expected.",
                category=UserWarning)
            algorithm.fit(X)

        t1 = time()
        if hasattr(algorithm, 'labels_'):
            y_pred = algorithm.labels_.astype(np.int)
        else:
            y_pred = algorithm.predict(X)

        plt.subplot(len(datasets), len(clustering_algorithms), plot_num)
        if i_dataset == 0:
            plt.title(name, size=18)

        colors = np.array(list(islice(cycle(['#377eb8', '#ff7f00', '#4daf4a',
                                             '#f781bf', '#a65628', '#984ea3',
                                             '#999999', '#e41a1c', '#dede00']),
                                      int(max(y_pred) + 1))))
        # Add black color for outliers (if any).
        colors = np.append(colors, ["#000000"])
        plt.scatter(X[:, 0], X[:, 1], s=10, color=colors[y_pred])

        plt.xlim(-2.5, 2.5)
        plt.ylim(-2.5, 2.5)
        plt.xticks(())
        plt.yticks(())
        plt.text(.99, .01, ('%.2fs' % (t1 - t0)).lstrip('0'),
                 transform=plt.gca().transAxes, size=15,
                 horizontalalignment='right')
        plot_num += 1
plt.suptitle('Clustering algorithms for N170 data')
plt.show()
