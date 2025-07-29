import json
import os
import sys

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC


def classify(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,  # stratify=y ensures train/test sets have similar class proportions
    )

    print(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
    print(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")
    print(f"Train set class distribution (y): {np.unique(y_train, return_counts=True)}")
    print(f"Test set class distribution (y): {np.unique(y_test, return_counts=True)}")

    model = SVC(kernel="linear", random_state=42)

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy on the test set: {accuracy:.4f}")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Class 0", "Class 1"]))


def main():
    if sys.gettrace():  # Check if in debugger
        spikes_filename = "slamdunk_short_B/2025-07-23T13-03-09wt_02212025_M_ACSF_slamdunk_short_B-00068_4d.npz"
        stims_filename = "slamdunk_short_B/2025-07-23T13-03-09wt_02212025_M_ACSF_slamdunk_short_B-00068.stims.json"
    elif len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <spikes4d.npz> <stims.json>")
        sys.exit(1)
    else:
        spikes_filename = sys.argv[1]
        stims_filename = sys.argv[2]

    # Check files
    for file_path in [spikes_filename, stims_filename]:
        if not os.path.exists(file_path):
            print(f"Error: {file_path} not found")
            sys.exit(1)

    try:
        spikes4d = np.load(spikes_filename)["array"]
        with open(stims_filename, "r") as f:
            stims = json.load(f)
        stimuli = stims["stimuli"]
        stimuli.pop(0)
        n_stimuli = len(stimuli)
        assert (
            n_stimuli == spikes4d.shape[0]
        ), "First dimension of spikes4d should be one less than number of stims"
        X = spikes4d.reshape((n_stimuli, -1))
        y = np.array([stim["bgColor"] == "white" for stim in stimuli])
        classify(X, y)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
