
from pathlib import Path
import h5py
import numpy as np


def create_hdf5(filepath, overwrite=False):
    """
    Create a new LOBSTER HDF5 archive.
    """

    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if filepath.exists() and not overwrite:
        raise FileExistsError(f"{filepath} already exists.")

    with h5py.File(filepath, "w") as h5:

        # Archive metadata
        h5.attrs["schema_version"] = "1.0"
        h5.attrs["lobster_version"] = "0.1.0"

        # Main metadata group
        h5.create_group("metadata")

    print(f"Created HDF5 archive: {filepath}")


def open_hdf5(filepath, mode="r"):
    """
    Open an existing HDF5 archive.

    Modes:
        'r'  : Read only
        'r+' : Read and write
        'a'  : Read and write; create if missing
    """

    filepath = Path(filepath)

    if not filepath.exists() and mode == "r":
        raise FileNotFoundError(filepath)

    return h5py.File(filepath, mode)


def close_hdf5(h5):
    """
    Close an open HDF5 archive.
    """

    if h5 is not None and h5.id.valid:
        h5.close()


def create_daily_group(h5, station, channel, date):
    """
    Create the station/channel/day hierarchy and its
    standard subgroups.
    """

    group_path = f"{station}/{channel}/{date}"

    if group_path in h5:
        raise ValueError(f"{group_path} already exists.")

    day = h5.create_group(group_path)

    # Daily metadata
    day.attrs["station"] = station
    day.attrs["channel"] = channel
    day.attrs["date_utc"] = date
    day.attrs["time_reference"] = "UTC"
    day.attrs["psd_scale"] = "linear"

    # Data products
    day.create_group("psd")
    day.create_group("statistics")
    day.create_group("quality")
    day.create_group("raw_data")

    return day


def write_daily_psd(
    day,
    frequency,
    hourly_median,
    hourly_window_count,
    hourly_mean=None,
    hourly_std=None,
    psd_units="",
):
    """
    Write daily PSD products.

    Expected dimensions:
        frequency:       (N_freq,)
        hourly PSDs:     (24, N_freq)
        window count:    (24,)
    """

    frequency = np.asarray(frequency, dtype=float)
    hourly_median = np.asarray(hourly_median, dtype=float)
    hourly_window_count = np.asarray(
        hourly_window_count, dtype=np.int32
    )

    # if frequency.ndim != 1:
    #     raise ValueError("frequency must be one-dimensional.")

    # if hourly_median.shape != (24, len(frequency)):
    #     raise ValueError("hourly_median must have shape (24, N_freq).")

    # if hourly_window_count.shape != 24:
    #     raise ValueError("hourly_window_count must have shape (24,).")

    psd = day["psd"]
    stats = day["statistics"]

    psd.create_dataset("frequency", data=frequency)
    psd.create_dataset(
        "hourly_median",
        data=hourly_median,
        compression="gzip",
    )

    if hourly_mean is not None:
        psd.create_dataset(
            "hourly_mean",
            data=np.asarray(hourly_mean, dtype=float),
            compression="gzip",
        )

    if hourly_std is not None:
        psd.create_dataset(
            "hourly_std",
            data=np.asarray(hourly_std, dtype=float),
            compression="gzip",
        )

    stats.create_dataset(
        "hourly_window_count",
        data=hourly_window_count,
    )

    psd.attrs["units"] = psd_units


def write_waveform_references(
    day,
    waveform_files,
    file_starttime,
    file_endtime,
    response_file=None,
):
    """
    Store references to the original waveform and response files.

    Times are Unix timestamps in UTC.
    """

    raw = day["raw_data"]

    waveform_files = [str(f) for f in waveform_files]
    file_starttime = np.asarray(file_starttime, dtype=float)
    file_endtime = np.asarray(file_endtime, dtype=float)

    if len(waveform_files) != len(file_starttime):
        raise ValueError("One start time is required per waveform file.")

    if len(waveform_files) != len(file_endtime):
        raise ValueError("One end time is required per waveform file.")

    string_dtype = h5py.string_dtype(encoding="utf-8")

    raw.create_dataset(
        "waveform_files",
        data=np.asarray(waveform_files, dtype=object),
        dtype=string_dtype,
    )

    raw.create_dataset("file_starttime", data=file_starttime)
    raw.create_dataset("file_endtime", data=file_endtime)

    if response_file is not None:
        raw.create_dataset(
            "response_file",
            data=str(response_file),
            dtype=string_dtype,
        )


def read_daily_psd(h5, station, channel, date):
    """
    Retrieve daily PSD data from an open HDF5 archive.
    """

    day = h5[f"{station}/{channel}/{date}"]

    psd = day["psd"]
    stats = day["statistics"]

    result = {
        "frequency": psd["frequency"][:],
        "hourly_median": psd["hourly_median"][:],
        "hourly_window_count": stats["hourly_window_count"][:],
        "metadata": dict(day.attrs),
    }

    for name in ("hourly_mean", "hourly_std"):
        if name in psd:
            result[name] = psd[name][:]

    return result
