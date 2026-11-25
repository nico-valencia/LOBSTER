from pathlib import Path

from .station import Station
from .channel import Channel

from ..io.metadata import read_metadata
from ..io.discovery import (
    discover_waveforms,
    discover_responses
)


class Dataset:
    """Represents an OBS deployment or experiment."""

    def __init__(
        self,
        name: str,
        data_dir: str | Path,
        response_dir: str | Path,
        metadata_file: str | Path
    ):

        self.name = name

        self.data_dir = Path(data_dir)
        self.response_dir = Path(response_dir)
        self.metadata_file = Path(metadata_file)

        self.stations = {}

        self._scanned = False

    def scan(self):
        """Discover files and construct the Dataset."""

        # Read input metadata.
        metadata = read_metadata(self.metadata_file)

        # print("Metadata keys:", list(metadata.keys())[:10])
        # print("Number of metadata stations:", len(metadata))

        # Discover waveform and response files.
        waveforms = discover_waveforms(self.data_dir)
        responses = discover_responses(self.response_dir)

        # Construct stations.
        station_names = set(metadata) # | set(waveforms) turning this off for now
        # print(station_names)

        for name in sorted(station_names):

            station_meta = metadata.get(name, {})
            # print(station_meta)

            def get_float(key):
                value = station_meta.get(key)

                if value is None or value.lower() in ("nan", "none", ""):
                    return None

                return float(value)

            station = Station(
                name=name,
                latitude=get_float("latitude"),
                longitude=get_float("longitude"),
                elevation=get_float("elevation"),
                deployment_date=(
                    station_meta.get("ondate")
                    or station_meta.get("deployment_date")
                ),
                recovery_date=(
                    station_meta.get("offdate")
                    or station_meta.get("recovery_date")
                ),
                instrument_type=station_meta.get("instrument_type"),
                sensors=station_meta.get("sensors"),
                metadata=station_meta
            )

            # Construct channels.
            station_waveforms = waveforms.get(name, {})

            network = station_meta.get("nwk", "")

            for channel_name, files in station_waveforms.items():

                channel = Channel(
                    name=channel_name,
                    waveform_files=files
                )

                # Match response files by network, station, and channel.
                candidates = [
                    response
                    for (net, sta, loc, chan), response
                    in responses.items()
                    if net == network
                    and sta == name
                    and chan == channel_name
                ]

                if len(candidates) > 1:
                    raise ValueError(
                        f"Ambiguous response match for "
                        f"{name}.{channel_name}"
                    )

                if candidates:
                    channel.response_file = candidates[0].get("resp")
                    channel.pz_file = candidates[0].get("pz")

                station.channels[channel_name] = channel

            self.stations[name] = station

        self._scanned = True

        return self

    def get_station(self, name: str) -> Station:
        return self.stations[name]

    def list_stations(self) -> list[str]:
        return sorted(self.stations.keys())

    @property
    def n_stations(self) -> int:
        return len(self.stations)

    def validate(self) -> list[str]:
        """Check for missing metadata and response files."""

        if not self._scanned:
            raise RuntimeError("Run scan() before validate().")

        issues = []

        for station in self.stations.values():

            if station.latitude is None:
                issues.append(f"{station.name}: Missing latitude")

            if station.longitude is None:
                issues.append(f"{station.name}: Missing longitude")

            if not station.channels:
                issues.append(f"{station.name}: No waveform channels found")

            for channel in station.channels.values():

                if channel.response_file is None:
                    issues.append(
                        f"{station.name}.{channel.name}: "
                        "No RESP file found"
                    )

        return issues