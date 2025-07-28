# Electrode labels copied from here
# https://www.multichannelsystems.com/sites/multichannelsystems.com/files/documents/data_sheets/120MEA_Layout.pdf
ELECTRODE_IDS_FILE_NAME = "electrode-ids.json"

import sys
import numpy as np
import json
from kilosort.io import save_probe

try:
    with open(ELECTRODE_IDS_FILE_NAME, "r") as file:
        labels = json.load(file)
except FileNotFoundError:
    print(f"${ELECTRODE_IDS_FILE_NAME} not found.")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: Could not parse JSON from file {ELECTRODE_IDS_FILE_NAME}")
    sys.exit(1)
# print(">>>>> labels=" + json.dumps(labels))

num_channels = len(labels)
pitch = 200  # microns
xc = np.zeros(num_channels)
yc = np.zeros(num_channels)

# Calculate position of each electrode (plus some that don't exist)
# Note there is no row "I"
positions = {}
letters = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M"]
for x in range(len(letters)):
    for y in range(12):
        label = f"{letters[x]}{y+1}"
        positions[label] = (x * pitch, y * pitch)
# print(">>>>> " + json.dumps(positions))

chanMap = np.arange(num_channels)  # Assuming all 120 channels are used

for i, label in enumerate(labels):
    if label in positions:
        xc[i], yc[i] = positions[label]
    else:
        print(f"Error: Label {label} not found in positions mapping.")
        sys.exit(1)

kcoords = np.zeros(num_channels)  # For a single 2D array

probe = {
    "chanMap": chanMap,
    "xc": xc,
    "yc": yc,
    "kcoords": kcoords,
    "n_chan": num_channels,
}

# Save the probe dictionary to JSON file
probe_filename = "120MEA200probe.json"
save_probe(probe, probe_filename)
print(f"Probe file saved to: {probe_filename}")
