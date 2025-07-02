# EEG ML Project with Muse Headset Data

## Overview
This project demonstrates an end-to-end pipeline for EEG signal analysis using Muse headset data:
- Preprocessing with MNE (filtering, ICA)
- Feature extraction: band power, connectivity, and Riemannian geometry features
- Classification using SVM, PyRiemann MDM, and PyTorch neural networks
- Visualizations including PSD and topographic scalp maps

## Dataset
Data sourced from Muse Muse2016 dataset (visual-N170 task).

## Usage
- Preprocess raw EEG signals
- Extract features with MNE and PyRiemann
- Train and evaluate classifiers
- Visualize EEG features and classification results

## Results
- Cross-validated classification accuracy ~58% with combined features
- Demonstrated feature fusion and neural network classification on consumer EEG data

## Requirements
- Python 3.13
- MNE, PyTorch, scikit-learn, PyRiemann, numpy, matplotlib

## Future work
- Feature attribution and interpretability
- CNN/RNN models for raw EEG time series
- Larger datasets and data augmentation
- Interactive visualization and demo app

---

### How to Run

See Jupyter Notebook. To be cleaned soon.
