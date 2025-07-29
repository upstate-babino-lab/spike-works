#!/usr/bin/env python
import numpy as np
import pandas as pd
import json
import sys
import os
from pathlib import Path


def generate_arrays(spike_file, synctones_file, stims_file):

    print(f"Processing: {spike_file}")

    # Load stimulus data to get individual durations
    print("Loading stimulus durations...")
    with open(stims_file, "r") as f:
        stims_data = json.load(f)
    stimuli = stims_data["stimuli"]

    # Load synctones
    synctones_df = pd.read_csv(synctones_file)
    synctones = synctones_df.iloc[:, 0].tolist()

    assert len(synctones) == (
        len(stimuli) - 1
    ), "Should have one less synctone than stimuli"

    # Remove first element of stimuli so it has same length as synctones.
    # Now each synctone identifies times starting timestamp of corresponding stim
    stimuli.pop(0)

    # Calculate individual stimulus durations and max duration
    stim_durations_ms = [stim["durationMs"] for stim in stimuli]
    max_duration_ms = max(stim_durations_ms)

    print(f"Stimulus durations: {min(stim_durations_ms)}ms - {max_duration_ms}ms")

    # Calculate time bins
    time_bin_size_ms = 20
    max_time_bins = int(np.ceil(max_duration_ms / time_bin_size_ms))
    bin_edges = np.linspace(0, (max_time_bins * time_bin_size_ms), max_time_bins + 1)

    print(f"{max_duration_ms=} {max_time_bins=}")
    print(f"{bin_edges=}")

    # Create stimulus intervals from synctones
    stim_intervals = []

    # Create intervals using planned durations (NOT synctone-to-synctone)
    for index, stim in enumerate(stimuli):
        start_time = synctones[index]
        planned_duration_s = stim_durations_ms[index] / 1000.0
        end_time = start_time + planned_duration_s
        stim_intervals.append((start_time, end_time))

    num_stimuli = len(stim_intervals)
    print(f"number of stim_intervals: {num_stimuli}")

    print("Processing spikes...")

    spikes_df = pd.read_csv(
        spike_file, header=1, names=["Channel", "Unit", "Timestamp"]
    )
    all_channels = sorted(spikes_df["Channel"].unique())
    all_units = sorted(spikes_df["Unit"].unique())

    shape = (num_stimuli, max_time_bins, len(all_channels), len(all_units))
    spike_array = np.zeros(shape, dtype=np.uint16)
    print(f"{spike_array.shape=}")
    memory_mb = spike_array.nbytes / (1024**2)
    print(f"Memory usage: {memory_mb:.1f} MB")

    for interval_idx, interval in enumerate(stim_intervals):
        (start, end) = interval
        interval_spikes = spikes_df[
            (spikes_df["Timestamp"] >= start) & (spikes_df["Timestamp"] < end)
        ].copy()
        interval_spikes["relative_time_ms"] = (
            interval_spikes["Timestamp"] - start
        ) * 1000
        for channel_idx, channel in enumerate(all_channels):
            for unit_idx, unit in enumerate(all_units):
                unit_spikes = interval_spikes[
                    (interval_spikes["Channel"] == channel)
                    & (interval_spikes["Unit"] == unit)
                ]
                unit_spike_times = unit_spikes["relative_time_ms"].values
                counts, _ = np.histogram(unit_spike_times, bins=bin_edges)
                spike_array[interval_idx, :, channel_idx, unit_idx] = counts

    n_spikes = int(spike_array.sum())

    # Create metadata
    metadata = {
        "shape": shape,
        "time_bin_ms": time_bin_size_ms,
        "max_stimulus_duration_ms": max_duration_ms,
        "max_time_bins": max_time_bins,
        "channels": len(all_channels),
        "units": len(all_units),
        "total_spikes": n_spikes,
        "stimulus_durations_ms": stim_durations_ms,
    }
    # print(json.dumps(metadata, indent=4))

    # Save files
    base_name = Path(spike_file).stem
    array_file = f"{base_name}_4d.npz"
    metadata_file = f"{base_name}_metadata.npz"

    np.savez_compressed(array_file, array=spike_array)
    np.savez_compressed(metadata_file, **metadata)

    print(f"Saved: {array_file}")
    print(f"Saved: {metadata_file}")

    return spike_array, metadata


def main():
    if sys.gettrace():  # Check if in debugger
        spike_file = "slamdunk_short_B/2025-07-23T13-03-09wt_02212025_M_ACSF_slamdunk_short_B-00068.txt"
        synctones_file = "slamdunk_short_B/2025-07-23T13-03-09wt_02212025_M_ACSF_slamdunk_short_B-00068_synctones.csv"
        stims_file = "slamdunk_short_B/2025-07-23T13-03-09wt_02212025_M_ACSF_slamdunk_short_B-00068.stims.json"
    elif len(sys.argv) != 4:
        print(
            f"Usage: {sys.argv[0]} <spike_file.txt> <synctones_file.csv> <stims.json>"
        )
        sys.exit(1)
    else:
        spike_file = sys.argv[1]
        synctones_file = sys.argv[2]
        stims_file = sys.argv[3]

    # Check files
    for file_path in [spike_file, synctones_file, stims_file]:
        if not os.path.exists(file_path):
            print(f"Error: {file_path} not found")
            sys.exit(1)

    try:
        spike_array, metadata = generate_arrays(spike_file, synctones_file, stims_file)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
