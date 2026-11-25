from dataclasses import dataclass, field
from pathlib import Path
from obspy import UTCDateTime


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


    def get_waveform_files(self, starttime, endtime):
        """
        Return waveform files within a specified UTC date range.

        Parameters
        ----------
        starttime : UTCDateTime
            Beginning of the requested time range.
        endtime : UTCDateTime
            End of the requested time range.

        Returns
        -------
        list
            Waveform file paths within the requested time range.
        """

        selected_files = []

        for file in self.waveform_files:

            filename = Path(file).name
            parts = filename.split(".")

            year = int(parts[2])
            julian_day = int(parts[3])

            file_time = UTCDateTime(
                year=year,
                julday=julian_day,
                hour=int(parts[4]),
                minute=int(parts[5]),
                second=int(parts[6])
            )

            if starttime <= file_time <= endtime:
                selected_files.append(file)

        return selected_files