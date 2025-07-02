# EEG-ExPy/examples/spectral_attention/README.md

### 🧠 Spectral Attention: Brain-Inspired Signal Focus for Better Learning

In this project, weare exploring **spectral attention**, a technique inspired by how the human brain processes sound and light frequencies. Instead of treating all input data equally, **spectral attention helps our AI system focus on the most informative frequency components** in EEG brainwave data.

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

### Agentic AI

An outline for an agent that can plug in any GitHub folder with EEG CSV data, and do all the processing and evaluation automatically:

import os
import glob
import mne
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

class EEGClassifierAgent:
    def __init__(self, data_folder, channel_names, label_column):
        self.data_folder = data_folder
        self.channel_names = channel_names
        self.label_column = label_column
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_and_preprocess(self):
        files = glob.glob(os.path.join(self.data_folder, "*.csv"))
        data_list = []
        labels = []
        for f in files:
            df = pd.read_csv(f)
            X = df[self.channel_names].values
            y = df[self.label_column].values
            data_list.append(X)
            labels.append(y)
        X_all = np.vstack(data_list)
        y_all = np.concatenate(labels)
        return X_all, y_all

    def extract_features(self, X):
        # Example: simple bandpower or statistical features per channel
        # Placeholder for your actual feature extraction pipeline
        features = np.log(np.mean(X**2, axis=1, keepdims=True) + 1e-6)  # power in log scale
        return features

    def prepare_dataset(self, X, y):
        X_feat = self.extract_features(X)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_feat)
        return train_test_split(X_scaled, y, test_size=0.2, stratify=y, random_state=42)

    def train_model(self, X_train, y_train):
        X_train_t = torch.tensor(X_train, dtype=torch.float32).to(self.device)
        y_train_t = torch.tensor(y_train, dtype=torch.long).to(self.device)
        dataset = TensorDataset(X_train_t, y_train_t)
        loader = DataLoader(dataset, batch_size=32, shuffle=True)

        model = nn.Sequential(
            nn.Linear(X_train.shape[1], 32),
            nn.ReLU(),
            nn.Linear(32, 2)
        ).to(self.device)

        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        model.train()
        for epoch in range(50):
            for xb, yb in loader:
                optimizer.zero_grad()
                out = model(xb)
                loss = criterion(out, yb)
                loss.backward()
                optimizer.step()
        return model

    def evaluate_model(self, model, X_test, y_test):
        model.eval()
        X_test_t = torch.tensor(X_test, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = model(X_test_t)
            probs = torch.softmax(outputs, dim=1)[:, 1].cpu().numpy()
            preds = outputs.argmax(dim=1).cpu().numpy()

        print("Classification Report:\n", classification_report(y_test, preds))
        print("Confusion Matrix:\n", confusion_matrix(y_test, preds))
        print(f"AUC Score: {roc_auc_score(y_test, probs):.4f}")

    def run(self):
        X, y = self.load_and_preprocess()
        X_train, X_test, y_train, y_test = self.prepare_dataset(X, y)
        model = self.train_model(X_train, y_train)
        self.evaluate_model(model, X_test, y_test)

# Usage example:
# agent = EEGClassifierAgent(data_folder="path/to/your/csvs",
#                            channel_names=['TP9','AF7','AF8','TP10'],
#                            label_column='stim')
# agent.run()









