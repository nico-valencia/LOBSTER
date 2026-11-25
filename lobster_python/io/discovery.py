from pathlib import Path
from collections import defaultdict


def discover_waveforms(data_dir: Path) -> dict:
    """
    Discover waveform files and organize them by station and channel.

    Expected filename:
    STATION.CHANNEL.YEAR.JULIANDAY.HOUR.MINUTE.SECOND.EXT

    Example:
    MM04.CH0.2019.323.00.30.59.msd
    """

    data_dir = Path(data_dir)

    if not data_dir.is_dir():
        raise NotADirectoryError(
            f"Waveform directory not found: {data_dir}"
        )

    waveforms = defaultdict(lambda: defaultdict(list))

    for file in data_dir.rglob("*"):

        if not file.is_file():
            continue

        parts = file.name.split(".")

        if len(parts) != 8:
            continue

        station, channel, year, jday, hour, minute, second, ext = parts

        # Check that the timestamp fields are numeric.
        try:
            year = int(year)
            jday = int(jday)
            hour = int(hour)
            minute = int(minute)
            second = int(second)
        except ValueError:
            continue

        if not (1 <= jday <= 366):
            continue

        waveforms[station][channel].append(file)

    return {
        station: {
            channel: sorted(files)
            for channel, files in channels.items()
        }
        for station, channels in waveforms.items()
    }


def discover_responses(response_dir: Path) -> dict:
    """
    Discover RESP and pole-zero files.

    Supports standard SEED-style response filenames:

    RESP.NETWORK.STATION.LOCATION.CHANNEL
    """

    response_dir = Path(response_dir)

    if not response_dir.is_dir():
        raise NotADirectoryError(
            f"Response directory not found: {response_dir}"
        )

    responses = defaultdict(dict)

    for file in response_dir.rglob("*"):

        if not file.is_file():
            continue

        parts = file.name.split(".")

        if len(parts) != 5 or parts[0] != "RESP":
            continue

        _, network, station, location, channel = parts

        # Determine whether this is a pole-zero file.
        is_pz = any(
            "pz" in part.lower()
            for part in file.parts
        )

        file_type = "pz" if is_pz else "resp"

        key = (network, station, location, channel)

        if file_type in responses[key]:
            raise ValueError(
                f"Multiple {file_type} files found for {key}"
            )

        responses[key][file_type] = file

    return dict(responses)