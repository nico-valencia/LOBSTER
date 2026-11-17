from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Channel:
    """Represents an individual seismic channel at an OBS station."""

    name: str

    waveform_files: list[Path] = field(default_factory=list)

    response_file: Path | None = None
    pz_file: Path | None = None

    sampling_rate: float | None = None
    azimuth: float | None = None
    dip: float | None = None

    def list_waveforms(self) -> list[Path]:
        """Return all waveform files associated with this channel."""
        return sorted(self.waveform_files)

    @property
    def n_waveforms(self) -> int:
        return len(self.waveform_files)