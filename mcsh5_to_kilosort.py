import os
from pathlib import Path
from open_mcsh5 import openMCSH5File
from write_kilosort_params import write_params
import spikeinterface.extractors as se
from kilosort import io  # Kilosort's I/O utilities for binary conversion
import numpy as np
from kilosort import run_kilosort


MCS_H5_FILE = Path(
    "/home/pwellner/Upstate-Babino/MEA-data/2025-07-23T13-03-09wt_02212025_M_ACSF_slamdunk_short_B-00068.h5",
)
OUTPUT_DIRECTORY = Path("kilosort_data/")
DATA_FILENAME = "kdata.bin"

mcs_recording = openMCSH5File(MCS_H5_FILE, stream_id=2)


# --- Create output directory if it doesn't exist ---
OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

# --- 2. Extract relevant metadata for Kilosort ---
sampling_frequency = mcs_recording["sampling_frequency"]
num_channels = mcs_recording["num_channels"]
channel_ids = mcs_recording["channel_ids"]
# You might need to verify the channel map and coordinates from the MCS data or provide a separate probe file.
# SpikeInterface can help export probe info if available in the recording object.

print(f"Sampling Frequency: {sampling_frequency} Hz")
print(f"Number of Channels: {num_channels}")

recording = se.NumpyRecording(
    traces_list=[mcs_recording["raw_data"]],
    sampling_frequency=sampling_frequency,
)


# --- 3. Convert to Kilosort's binary format ---
# This function handles reading the recording chunks and writing them to a binary file
# with the correct data type and order.
# The 'io.spikeinterface_to_binary' function also handles writing probe information
# if it's available in the SpikeInterface RecordingExtractor.
# It returns filename, N_samples, N_channels, sampling_frequency, probe_path
try:
    filename_bin, N_samples, N_channels, N_segments, fs, probe_path = (
        io.spikeinterface_to_binary(
            recording,
            OUTPUT_DIRECTORY,
            data_name=DATA_FILENAME,
            dtype=mcs_recording["raw_data"].dtype,
            chunksize=60000,  # Adjust chunksize based on your system's RAM
            export_probe=True,  # Export probe info if available, as a .prb file
        )
    )

    print(f"\nSuccessfully converted to binary:")
    print(f"  Binary file: {filename_bin}")
    print(f"  Number of samples: {N_samples}")
    print(f"  Number of channels: {N_channels}")
    print(f"  Number of segments: {N_segments}")
    print(f"  Sampling frequency: {fs}")
    print(f"  Probe file (if exported): {probe_path}")

    kilosort_settings = {
        # Essential parameters for Kilosort4 to load data:
        "filename": OUTPUT_DIRECTORY / DATA_FILENAME,  # Name of the binary data file
        "n_chan_bin": N_channels,  # Number of channels in the binary file
        "fs": fs,  # Sampling frequency
        "probe_path": "",  # Path to the probe file relative to params.py
        # Data types:
        "dtype": str(
            mcs_recording["raw_data"].dtype
        ),  # Match the dtype of the binary file
    }
    write_params(kilosort_settings, OUTPUT_DIRECTORY)

except Exception as e:
    print(f"Error during binary conversion: {e}")


# DEBUG only: test if kilosort can run
ops, st, clu, tF, Wall, similar_templates, is_ref, est_contam_rate, kept_spikes = (
    run_kilosort(
        settings=kilosort_settings, results_dir="results", verbose_console=True
    )
)

print("Kilosort4 sorting complete!")
print(f"Results are typically saved in: {os.path.join(OUTPUT_DIRECTORY, 'kilosort4')}")
