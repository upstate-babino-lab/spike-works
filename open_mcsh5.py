# Slightly modified version of spikeinterface/src/spikeinterface/extractors/mcsh5extractors.py
# https://github.com/SpikeInterface/spikeinterface/blob/705d194f811b738003b0afe5c786d064cbb16b40/src/spikeinterface/extractors/mcsh5extractors.py#L17
# Avoids the assert on validity of 'ChannelDataTimeStamps'

import h5py
import numpy as np
import spikeinterface.extractors as se


def openMCSH5File(filename, stream_id):
    """Open an MCS hdf5 file, read and return the recording info.
    Specs can be found online
    https://www.multichannelsystems.com/downloads/documentation?page=3
    """

    rf = h5py.File(filename, "r")

    stream_name = "Stream_" + str(stream_id)
    analog_stream_names = list(
        rf.require_group("/Data/Recording_0/AnalogStream").keys()
    )
    assert stream_name in analog_stream_names, (
        f"Specified stream does not exist. " f"Available streams: {analog_stream_names}"
    )

    stream = rf.require_group("/Data/Recording_0/AnalogStream/" + stream_name)
    data = np.array(stream.get("ChannelData")).T
    timestamps = np.array(stream.get("ChannelDataTimeStamps"))
    info = np.array(stream.get("InfoChannel"))
    dtype = data.dtype

    Unit = info["Unit"][0]
    Tick = info["Tick"][0] / 1e6
    exponent = info["Exponent"][0]
    convFact = info["ConversionFactor"][0]
    gain_uV = 1e6 * (convFact.astype(float) * (10.0**exponent))
    offset_uV = -1e6 * (info["ADZero"].astype(float) * (10.0**exponent)) * gain_uV

    (
        nFrames,
        nRecCh,
    ) = data.shape
    channel_ids = [f"Ch{ch}" for ch in info["ChannelID"]]
    assert len(np.unique(channel_ids)) == len(
        channel_ids
    ), "Duplicate MCS channel IDs found"
    electrodeLabels = [l.decode() for l in info["Label"]]

    assert (
        timestamps[0][1] < timestamps[0][2]
    ), "Please check the validity of 'ChannelDataTimeStamps' in the stream."
    TimeVals = np.arange(timestamps[0][1], timestamps[0][2] + 1, 1) * Tick

    if Unit != b"V":
        print(
            f"Unexpected units found, expected volts, found {Unit.decode('UTF-8')}. Assuming Volts."
        )

    timestep_avg = np.mean(TimeVals[1:] - TimeVals[0:-1])
    timestep_min = np.min(TimeVals[1:] - TimeVals[0:-1])
    timestep_max = np.min(TimeVals[1:] - TimeVals[0:-1])
    assert all(
        np.abs(np.array((timestep_min, timestep_max)) - timestep_avg) / timestep_avg
        < 1e-6
    ), "Time steps vary by more than 1 ppm"
    samplingRate = 1.0 / timestep_avg

    mcs_info = {
        "raw_data": data,
        "filehandle": rf,
        "num_frames": nFrames,
        "sampling_frequency": samplingRate,
        "num_channels": nRecCh,
        "channel_ids": channel_ids,
        "electrode_labels": electrodeLabels,
        "gain": gain_uV,
        "dtype": dtype,
        "offset": offset_uV,
    }

    return mcs_info
