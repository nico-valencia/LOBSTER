
from pathlib import Path
from obspy import read_inventory
import numpy as np
from obspy import UTCDateTime


def check_response_metadata(trace, inventory):
    """
    Compare waveform identifiers with the identifiers in a RESP Inventory.

    Returns
    -------
    response_metadata : dict
        Identifiers read from the response Inventory.
    mismatches : list
        Descriptions of differences between waveform and response metadata.
    """

    if (
        len(inventory.networks) != 1
        or len(inventory[0].stations) != 1
        or len(inventory[0][0].channels) != 1
    ):
        raise ValueError(
            "Expected exactly one network, station, and channel "
            "in the response Inventory."
        )

    response_channel = inventory[0][0][0]

    fields = {
        "network": (trace.stats.network, inventory[0].code),
        "station": (trace.stats.station, inventory[0][0].code),
        "location": (
            trace.stats.location,
            response_channel.location_code
        ),
        "channel": (trace.stats.channel, response_channel.code),
    }

    response_metadata = {
        field: values[1]
        for field, values in fields.items()
    }

    mismatches = []

    for field, (waveform_value, response_value) in fields.items():
        if waveform_value != response_value:
            mismatches.append(
                f"{field}: waveform='{waveform_value}', "
                f"RESP='{response_value}'"
            )

    return response_metadata, mismatches


def remove_response(
    trace,
    response_file=None,
    inventory=None,
    pre_filt=(0.005, 0.01, 20.0, 25.0),
    output="VEL"
):
    """
    Remove the instrument response from an ObsPy Trace.

    Parameters
    ----------
    trace : obspy.Trace
        Waveform to correct.
    response_file : str or Path, optional
        Path to the assigned RESP file.
    inventory : obspy.Inventory, optional
        Previously loaded response Inventory. Supplying this avoids
        repeatedly reading the same RESP file.
    pre_filt : tuple
        Four-corner frequency pre-filter.
    output : str
        Desired physical output units: "VEL", "DISP", or "ACC".

    Returns
    -------
    obspy.Trace
        Response-corrected copy of the input trace.

    Notes
    -----
    If waveform and RESP identifiers differ, a warning is printed.
    The response Inventory identifiers are then changed to match the
    waveform. The response itself is not modified.
    """

    corrected_trace = trace.copy()

    # Load the response Inventory if one was not supplied.
    if inventory is None:

        if response_file is None:
            raise ValueError(
                "Provide either response_file or inventory."
            )

        response_file = Path(response_file)

        if not response_file.is_file():
            raise FileNotFoundError(
                f"Response file not found: {response_file}"
            )

        inventory = read_inventory(
            str(response_file),
            format="RESP"
        )

    # Work with a copy so the caller's Inventory is unchanged.
    inventory = inventory.copy()

    # Compare waveform and response identifiers.
    response_metadata, mismatches = check_response_metadata(
        corrected_trace,
        inventory
    )

    if mismatches:
        print(f"\nWARNING: RESP metadata mismatch for {trace.id}")

        if response_file is not None:
            print(f"Response file: {response_file}")

        for mismatch in mismatches:
            print(f"  - {mismatch}")

        print("Continuing with the assigned response file.\n")

    # Remap identifiers so ObsPy associates this response with the trace.
    inventory[0].code = corrected_trace.stats.network
    inventory[0][0].code = corrected_trace.stats.station
    inventory[0][0][0].location_code = corrected_trace.stats.location
    inventory[0][0][0].code = corrected_trace.stats.channel

    # Remove the instrument response.
    corrected_trace.remove_response(
        inventory=inventory,
        output=output,
        pre_filt=pre_filt
    )

    return corrected_trace



def extract_time_window(trace, starttime, endtime):
    """
    Extract a time interval from an ObsPy Trace.

    The interval is half-open: [starttime, endtime).
    The start is included and the end is excluded.

    Parameters
    ----------
    trace : obspy.Trace
        Input waveform.
    starttime : UTCDateTime or compatible value
        Beginning of the requested interval.
    endtime : UTCDateTime or compatible value
        End of the requested interval.

    Returns
    -------
    obspy.Trace
        A copy containing only the requested samples.
    """

    starttime = UTCDateTime(starttime)
    endtime = UTCDateTime(endtime)

    if endtime <= starttime:
        raise ValueError("endtime must be later than starttime.")

    sampling_rate = trace.stats.sampling_rate
    delta = trace.stats.delta

    # Convert requested times to sample indices.
    i0 = int(np.ceil(
        (starttime - trace.stats.starttime) * sampling_rate - 1e-10
    ))

    i1 = int(np.ceil(
        (endtime - trace.stats.starttime) * sampling_rate - 1e-10
    ))

    # Restrict indices to the available data.
    i0 = max(0, i0)
    i1 = min(trace.stats.npts, i1)

    if i1 <= i0:
        raise ValueError(
            "Requested time window contains no samples "
            "from this trace."
        )

    # Copy the trace and replace its data with the selected samples.
    segment = trace.copy()
    segment.data = trace.data[i0:i1].copy()

    # Update the segment's start time.
    segment.stats.starttime = (
        trace.stats.starttime + i0 * delta
    )

    return segment


# from obspy import UTCDateTime

def sliding_windows(tr, window_minutes):
    """
    Generate 50% overlapping windows from an ObsPy Trace.

    Parameters
    ----------
    tr : obspy.Trace
        Input waveform.
    window_minutes : float
        Window duration in minutes.

    Yields
    ------
    obspy.Trace
        Individual waveform windows.
    """

    window = window_minutes * 60
    step = window / 2

    start = tr.stats.starttime
    end = tr.stats.endtime

    current_time = start

    while current_time + window <= end:
        window_trace = tr.slice(
            starttime=current_time,
            endtime=current_time + window
        )

        yield window_trace

        current_time += step