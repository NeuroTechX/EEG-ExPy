# EEG-ExPy/examples/spectral_attention/README.md

### 🧠 Spectral Attention: Brain-Inspired Signal Focus for Better Learning

In this project, we're exploring **spectral attention**, a technique inspired by how the human brain processes sound and light frequencies. Instead of treating all input data equally, **spectral attention helps our AI system focus on the most informative frequency components** in EEG brainwave data.

Imagine listening to a conversation in a noisy room — your brain naturally tunes in to the important frequencies of speech and filters out irrelevant noise. **Our model does the same**, identifying which parts of the brain signal (in the frequency spectrum) are most relevant for tasks like emotion detection, attention analysis, or neurological monitoring.

Technically, we apply **Fourier transforms** to convert time-based EEG signals into their frequency spectrum, then use attention mechanisms to let the model "choose" the most valuable frequency bands to focus on. This improves accuracy and interpretability, while mimicking how biological systems optimize their perception.

This approach can lead to smarter brain-computer interfaces, better diagnostics for neurological diseases, and more energy-efficient ML models inspired by nature.

## EEG ML Project with Muse Headset Data

### Overview
This project demonstrates an end-to-end pipeline for EEG signal analysis using Muse headset data:
- Preprocessing with MNE (filtering, ICA)
- Feature extraction: band power, connectivity, and Riemannian geometry features
- Classification using SVM, PyRiemann MDM, and PyTorch neural networks
- Visualizations including PSD and topographic scalp maps

### Dataset
Data sourced from Muse Muse2016 dataset (visual-N170 task).

### Usage
- Preprocess raw EEG signals
- Extract features with MNE and PyRiemann
- Train and evaluate classifiers
- Visualize EEG features and classification results

### Results
- Cross-validated classification accuracy ~58% with combined features
- Demonstrated feature fusion and neural network classification on consumer EEG data

### Requirements
- Python 3.13
- MNE, PyTorch, scikit-learn, PyRiemann, numpy, matplotlib

### Future work
- Feature attribution and interpretability (partly done)
- CNN/RNN models for raw EEG time series (partly done)
- Larger datasets and data augmentation
- Interactive visualization and demo app

---

### How to Run

See [Jupyter Notebook](https://github.com/yashineonline/EEG-ExPy/blob/master/examples/spectral_attention/spectral_attention.ipynb). 

To be cleaned up soon.


# EEG Classification Pipeline Summary

## Final Model Performance

- **Accuracy:** 0.73  
- **AUC (Area Under ROC Curve):** 0.8571  
- **Confusion Matrix:**

|               | Predicted Negative | Predicted Positive |
|---------------|--------------------|--------------------|
| **Actual Negative** | TN = 10             | FP = 6              |
| **Actual Positive** | FN = 2              | TP = 12             |

---

## 🧠 What this Confirms

| Metric          | Interpretation                             |
|-----------------|--------------------------------------------|
| **AUC = 0.8571**| Model is good at distinguishing classes    |
| **Accuracy = 0.73** | Balanced accuracy indicating realistic performance |
| **Confusion Matrix**| Catches most positives (TP=12, FN=2)      |
| **Precision/Recall** | Good balance between false positives and false negatives |

---

## Next Steps

- This model demonstrates strong potential for EEG-based visual stimulus classification.
- Ready to extend to larger datasets for more robust validation.
- Next: Automate pipeline execution for arbitrary EEG datasets to facilitate reproducible research.







