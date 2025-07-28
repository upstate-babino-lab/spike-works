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

sampling_frequency = mcs_recording["sampling_frequency"]
num_channels = mcs_recording["num_channels"]
channel_ids = mcs_recording["channel_ids"]
dtype = str(mcs_recording["raw_data"].dtype)

print(f"Sampling Frequency: {sampling_frequency} Hz")
print(f"Number of Channels: {num_channels}")
print(f"dtype: {dtype}")

recording = se.NumpyRecording(
    traces_list=[mcs_recording["raw_data"]],
    sampling_frequency=sampling_frequency,
)


try:
    filename_bin, N_samples, N_channels, N_segments, fs, probe_path = (
        io.spikeinterface_to_binary(
            recording,
            OUTPUT_DIRECTORY,
            data_name=DATA_FILENAME,
            dtype=dtype,
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
        "filename": OUTPUT_DIRECTORY / DATA_FILENAME,
        "n_chan_bin": N_channels,
        "fs": fs,  # Sampling frequency
        "probe_path": "",
    }
    write_params(kilosort_settings, OUTPUT_DIRECTORY)

except Exception as e:
    print(f"Error during binary conversion: {e}")


# DEBUG only: test if kilosort can run
probe_dict = io.load_probe("120MEA200probe.json")
print("\n\nRunning kilosort...")
ops, st, clu, tF, Wall, similar_templates, is_ref, est_contam_rate, kept_spikes = (
    run_kilosort(
        settings=kilosort_settings,
        data_dtype=dtype,
        results_dir="results",
        verbose_console=True,
        probe=probe_dict,
    )
)

print("Kilosort4 sorting complete!")
print(f"Results are typically saved in: {os.path.join(OUTPUT_DIRECTORY, 'kilosort4')}")
