import csv
from pathlib import Path

def read_metadata(metadata_file: Path) -> dict:

    metadata_file = Path(metadata_file)

    if not metadata_file.is_file():
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

    metadata = {}

    with open(metadata_file, "r", newline="", encoding="utf-8-sig") as f:

        reader = csv.DictReader(f, delimiter=",")

        for row in reader:

            # Normalize column names and values.
            row = {
                key.strip().lower(): value.strip() if value else None
                for key, value in row.items()
                if key is not None
            }

            station_name = row.get("station")

            if not station_name:
                continue

            if station_name in metadata:
                raise ValueError(f"Duplicate station: {station_name}")

            metadata[station_name] = row

    return metadata