from dataclasses import dataclass, field

from .channel import Channel


@dataclass
class Station:
    """Represents an individual OBS station."""

    name: str

    latitude: float | None = None
    longitude: float | None = None
    elevation: float | None = None

    deployment_date: str | None = None
    recovery_date: str | None = None

    instrument_type: str | None = None
    sensors: str | None = None

    channels: dict[str, Channel] = field(default_factory=dict)

    # Retain additional fields from the deployment metadata.
    metadata: dict = field(default_factory=dict)

    def get_channel(self, name: str) -> Channel:
        return self.channels[name]

    def list_channels(self) -> list[str]:
        return sorted(self.channels.keys())

    @property
    def n_channels(self) -> int:
        return len(self.channels)