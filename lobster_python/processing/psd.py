
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import welch
from obspy import read, read_inventory, UTCDateTime


def check_response_metadata(trace, inventory):
    """
    Compare waveform metadata with the metadata in a RESP Inventory.

    Parameters
    ----------
    trace : obspy.Trace
        Waveform trace.
    inventory : obspy.Inventory
        Inventory containing the assigned instrument response.

    Returns
    -------
    response_metadata : dict
        Identifiers read from the response Inventory.
    mismatches : list
        Descriptions of differences between waveform and response metadata.
    """

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


def preprocess_trace(
    trace,
    remove_response=True,
    response_file=None,
    response_inventory=None,
    pre_filt=(0.005, 0.01, 20.0, 25.0),
    output="VEL"
):
    """
    Detrend a trace and optionally remove its instrument response.

    Parameters
    ----------
    trace : obspy.Trace
        Waveform trace.
    remove_response : bool
        Whether to remove the instrument response.
    response_file : Path, optional
        RESP file associated with the channel.
    response_inventory : obspy.Inventory, optional
        Previously loaded response Inventory. If not supplied, it is
        read from response_file.
    pre_filt : tuple
        Four-corner frequency pre-filter.
    output : str
        Physical output units: VEL, DISP, or ACC.

    Returns
    -------
    obspy.Trace
        Processed waveform trace.
    """

    trace = trace.copy()

    # Remove mean and linear trend.
    trace.detrend(type="demean")
    trace.detrend(type="linear")

    if remove_response:

        if response_inventory is None:

            if response_file is None:
                raise ValueError("No response file supplied.")

            response_inventory = read_inventory(
                str(response_file),
                format="RESP"
            )

        # Work on a copy so the original Inventory remains unchanged.
        response_inventory = response_inventory.copy()

        # This implementation expects one response channel per file.
        if (
            len(response_inventory.networks) != 1
            or len(response_inventory[0].stations) != 1
            or len(response_inventory[0][0].channels) != 1
        ):
            raise ValueError(
                f"Expected exactly one response channel in "
                f"{response_file}"
            )

        # Compare waveform and response metadata.
        response_metadata, mismatches = check_response_metadata(
            trace, response_inventory
        )

        # Notify the user of metadata discrepancies.
        if mismatches:

            print(f"\nWARNING: RESP metadata mismatch for {trace.id}")

            if response_file is not None:
                print(f"Response file: {response_file}")

            for mismatch in mismatches:
                print(f"  - {mismatch}")

            print("Continuing with the assigned response file.\n")

        # Remap the Inventory identifiers to match the waveform.
        # The underlying instrument response is not modified.
        response_inventory[0].code = trace.stats.network
        response_inventory[0][0].code = trace.stats.station
        response_inventory[0][0][0].location_code = trace.stats.location
        response_inventory[0][0][0].code = trace.stats.channel

        # Remove instrument response.
        trace.remove_response(
            inventory=response_inventory,
            output=output,
            pre_filt=pre_filt
        )

    return trace


def calculate_psd(data, sampling_rate, window_seconds=1000):
    """
    Calculate the power spectral density using Welch's method.

    Parameters
    ----------
    data : array-like
        Waveform samples.
    sampling_rate : float
        Sampling rate in Hz.
    window_seconds : float
        Welch segment length in seconds.

    Returns
    -------
    frequencies : ndarray or None
        Frequency values in Hz.
    power : ndarray or None
        Power spectral density.
    """

    nperseg = min(
        int(window_seconds * sampling_rate),
        len(data)
    )

    if nperseg < 2:
        return None, None

    frequencies, power = welch(
        data,
        fs=sampling_rate,
        nperseg=nperseg,
        return_onesided=True,
        scaling="density"
    )

    # Preserve the original upper frequency limit of approximately 2 Hz.
    mask = frequencies <= 2.0

    return frequencies[mask], power[mask]


def save_psd(
    frequencies,
    power,
    output_dir,
    station,
    channel,
    timestamp
):
    """
    Save PSD data and its corresponding PDF plot.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data_file = output_dir / "PSD.dat"
    plot_file = output_dir / "PSD.pdf"

    # Save frequency and PSD columns.
    np.savetxt(
        data_file,
        np.column_stack((frequencies, power)),
        header="Frequency PSD"
    )

    # Generate PSD plot.
    fig, ax = plt.subplots()

    ax.loglog(frequencies[1:], power[1:])

    ax.set(
        xlabel="Frequency (Hz)",
        ylabel="PSD",
        title=f"{station} {channel} {timestamp}"
    )

    fig.tight_layout()
    fig.savefig(plot_file)
    plt.close(fig)


def process_channel(
    station,
    channel,
    output_dir="PSD_dir",
    remove_response=True,
    pre_filt=(0.005, 0.01, 20.0, 25.0),
    output_units="VEL",
    window_seconds=1000,
    overwrite=False
):
    """
    Calculate hourly PSDs for all waveform files associated with a channel.

    Output hierarchy
    ----------------
    output_dir/
        station/
            year/
                month/
                    day/
                        hour/
                            channel/
                                PSD.dat
                                PSD.pdf

    Parameters
    ----------
    station : lobster.Station
        Station object.
    channel : lobster.Channel
        Channel object.
    output_dir : str or Path
        Root directory for PSD outputs.
    remove_response : bool
        Whether to remove the instrument response (default: True).
    pre_filt : tuple
        Four-corner frequency pre-filter for response removal.
    output_units : str
        Physical output units: VEL, DISP, or ACC.
    window_seconds : float
        Welch segment length in seconds.
    overwrite : bool
        Whether to overwrite existing PSD files.
    """

    output_dir = Path(output_dir)

    # Load the response Inventory once per channel.
    response_inventory = None

    if remove_response:

        if channel.response_file is None:
            raise ValueError(
                f"No response file assigned to "
                f"{station.name}.{channel.name}"
            )

        if not Path(channel.response_file).is_file():
            raise FileNotFoundError(
                f"Response file not found: {channel.response_file}"
            )

        response_inventory = read_inventory(
            str(channel.response_file),
            format="RESP"
        )

    # Process waveform files.
    for waveform_file in channel.waveform_files:

        stream = read(str(waveform_file))

        for trace in stream:

            # Detrend and optionally remove instrument response.
            trace = preprocess_trace(
                trace,
                remove_response=remove_response,
                response_file=channel.response_file,
                response_inventory=response_inventory,
                pre_filt=pre_filt,
                output=output_units
            )

            fs = trace.stats.sampling_rate

            start = trace.stats.starttime
            end = trace.stats.endtime

            # Find the beginning of the first UTC hour.
            hour_start = UTCDateTime(
                year=start.year,
                julday=start.julday,
                hour=start.hour
            )

            # Process each hour intersected by the trace.
            while hour_start <= end:

                hour_end = hour_start + 3600

                # Determine sample indices for this hourly interval.
                i0 = max(
                    0,
                    int(np.ceil((hour_start - start) * fs - 1e-8))
                )

                i1 = min(
                    trace.stats.npts,
                    int(np.ceil((hour_end - start) * fs - 1e-8))
                )

                data = trace.data[i0:i1]

                if len(data) >= 2:

                    frequencies, power = calculate_psd(
                        data,
                        fs,
                        window_seconds=window_seconds
                    )

                    if frequencies is not None:

                        timestamp = hour_start.strftime(
                            "%Y-%m-%d %H:00"
                        )

                        # Preserve original output hierarchy.
                        folder = (
                            output_dir
                            / station.name
                            / str(hour_start.year)
                            / str(hour_start.month)
                            / str(hour_start.day)
                            / str(hour_start.hour)
                            / channel.name
                        )

                        # Skip existing results unless overwriting.
                        if (
                            not overwrite
                            and (folder / "PSD.dat").exists()
                        ):
                            hour_start += 3600
                            continue

                        save_psd(
                            frequencies,
                            power,
                            folder,
                            station.name,
                            channel.name,
                            timestamp
                        )

                hour_start += 3600

# from pathlib import Path

# import numpy as np
# import matplotlib.pyplot as plt
# from scipy.signal import welch
# from obspy import read, UTCDateTime


# def check_response_metadata(trace, response_file):
#     """
#     Compare waveform metadata with the metadata in a RESP file.

#     Returns a list of mismatch descriptions. Mismatches are warnings,
#     not errors: the response can still be used.
#     """
#     fields = {
#         "network": trace.stats.network,
#         "station": trace.stats.station,
#         "location": trace.stats.location,
#         "channel": trace.stats.channel,
#     }

#     response_metadata = {}

#     with open(response_file, "r", encoding="utf-8") as f:
#         for line in f:
#             if "B050F03" in line:
#                 response_metadata["station"] = line.split(":", 1)[1].strip()
#             elif "B050F16" in line:
#                 response_metadata["network"] = line.split(":", 1)[1].strip()
#             elif "B052F03" in line:
#                 response_metadata["location"] = line.split(":", 1)[1].strip()
#             elif "B052F04" in line:
#                 response_metadata["channel"] = line.split(":", 1)[1].strip()

#     mismatches = []

#     for field, waveform_value in fields.items():
#         response_value = response_metadata.get(field)

#         if response_value is not None and waveform_value != response_value:
#             mismatches.append(
#                 f"{field}: waveform='{waveform_value}', "
#                 f"RESP='{response_value}'"
#             )

#     return response_metadata, mismatches



# def preprocess_trace(
#     trace,
#     remove_response=True,
#     response_file=None,
#     pre_filt=(0.005, 0.01, 20.0, 25.0),
#     output="VEL"
# ):
#     """
#     Detrend a trace and optionally remove its instrument response.
#     """

#     trace = trace.copy()

#     trace.detrend(type="demean")
#     trace.detrend(type="linear")

#     if remove_response:

#         if response_file is None:
#             raise ValueError("No response file supplied.")

#         response_metadata, mismatches = check_response_metadata(
#             trace, response_file
#         )

#         if mismatches:
#             print(f"\nWARNING: RESP metadata mismatch for {trace.id}")
#             print(f"Response file: {response_file}")

#             for mismatch in mismatches:
#                 print(f"  - {mismatch}")

#             print("Continuing with the assigned response file.\n")

#         required_fields = ["network", "station", "location", "channel"]

#         missing_fields = [
#             field for field in required_fields
#             if field not in response_metadata
#         ]

#         if missing_fields:
#             raise ValueError(
#                 f"Could not read {missing_fields} from RESP file: "
#                 f"{response_file}"
#             )

#         seedresp = {
#             "filename": str(response_file),
#             "date": trace.stats.starttime,
#             "units": output,
#             "network": response_metadata["network"],
#             "station": response_metadata["station"],
#             "location": response_metadata["location"],
#             "channel": response_metadata["channel"],
#         }

#         trace.simulate(
#             pre_filt=pre_filt,
#             seedresp=seedresp
#         )

#     return trace



# def calculate_psd(data, sampling_rate, window_seconds=1000):
#     """
#     Calculate PSD using Welch's method.
#     """

#     nperseg = min(
#         int(window_seconds * sampling_rate),
#         len(data)
#     )

#     if nperseg < 2:
#         return None, None

#     frequencies, power = welch(
#         data,
#         fs=sampling_rate,
#         nperseg=nperseg,
#         return_onesided=True,
#         scaling="density"
#     )

#     # Preserve the approximate frequency range of the original code.
#     mask = frequencies <= 2.0

#     return frequencies[mask], power[mask]


# def save_psd(
#     frequencies,
#     power,
#     output_dir,
#     station,
#     channel,
#     timestamp
# ):
#     """
#     Save PSD data and PDF plot.
#     """

#     output_dir.mkdir(parents=True, exist_ok=True)

#     data_file = output_dir / "PSD.dat"
#     plot_file = output_dir / "PSD.pdf"

#     np.savetxt(
#         data_file,
#         np.column_stack((frequencies, power)),
#         header="Frequency PSD"
#     )

#     fig, ax = plt.subplots()

#     ax.loglog(frequencies, power)

#     ax.set(
#         xlabel="Frequency (Hz)",
#         ylabel="PSD",
#         title=f"{station} {channel} {timestamp}"
#     )

#     fig.savefig(plot_file)
#     plt.close(fig)


# def process_channel(
#     station,
#     channel,
#     output_dir="PSD_dir",
#     remove_response=True,
#     pre_filt=(0.005, 0.01, 20.0, 25.0),
#     output_units="VEL",
#     window_seconds=1000,
#     overwrite=False
# ):
#     """
#     Calculate hourly PSDs for all waveform files belonging to a channel.

#     Output hierarchy:
#         output_dir/
#             station/
#                 year/
#                     month/
#                         day/
#                             hour/
#                                 channel/
#                                     PSD.dat
#                                     PSD.pdf
#     """

#     for waveform_file in channel.waveform_files:

#         stream = read(str(waveform_file))

#         for trace in stream:

#             trace = preprocess_trace(
#                 trace,
#                 remove_response=remove_response,
#                 response_file=channel.response_file,
#                 pre_filt=pre_filt,
#                 output=output_units
#             )

#             fs = trace.stats.sampling_rate
#             start = trace.stats.starttime
#             end = trace.stats.endtime

#             # Find the first UTC hour intersecting the trace.
#             hour_start = UTCDateTime(
#                 year=start.year,
#                 julday=start.julday,
#                 hour=start.hour
#             )

#             if hour_start > start:
#                 hour_start -= 3600

#             while hour_start <= end:

#                 hour_end = hour_start + 3600

#                 # Extract samples within this hour.
#                 i0 = max(
#                     0,
#                     int(np.ceil((hour_start - start) * fs - 1e-8))
#                 )

#                 i1 = min(
#                     trace.stats.npts,
#                     int(np.ceil((hour_end - start) * fs - 1e-8))
#                 )

#                 data = trace.data[i0:i1]

#                 if len(data) >= 2:

#                     frequencies, power = calculate_psd(
#                         data,
#                         fs,
#                         window_seconds=window_seconds
#                     )

#                     timestamp = hour_start.strftime(
#                         "%Y-%m-%d %H:00"
#                     )

#                     # Preserve the original directory hierarchy.
#                     folder = (
#                         Path(output_dir)
#                         / station.name
#                         / str(hour_start.year)
#                         / str(hour_start.month)
#                         / str(hour_start.day)
#                         / str(hour_start.hour)
#                         / channel.name
#                     )

#                     if not overwrite and (folder / "PSD.dat").exists():
#                         hour_start += 3600
#                         continue

#                     if frequencies is not None:
#                         save_psd(
#                             frequencies,
#                             power,
#                             folder,
#                             station.name,
#                             channel.name,
#                             timestamp
#                         )

#                 hour_start += 3600