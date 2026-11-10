# LOBSTER contract

In order for the workflow to work with either Python or MATLAB, both languages must be able to read and write what the other language does. This document is meant to cover everything shared between the two. 

## 1. Config

- One JSON file per experiment, in `config/`. `config/PacORCA.json` is the template.
- JSON has no comments, so every field is documented in section 7 below.
- Both languages load the config at the top of every script (`jsondecode` in MATLAB, `json.load` in Python) and pass the resulting object into library functions. No library function reads a global or hardcodes a path.
- `null` means "not yet decided." A script that needs a `null` value must stop with a clear error naming the field.
- Path values may contain `{root}` and other `paths` keys in braces. Both languages implement the same small resolver: substitute `{key}` from the `paths` block repeatedly until no braces from `paths` remain.
- Filename patterns use these tokens (resolved by each language's resolver, never by `sprintf`/`format` specs, because those differ between languages):

| Token | Meaning | Example |
|---|---|---|
| `{station}` | station code | `MM04` |
| `{network}` | network code | `XX` |
| `{channel}` | channel code | `BH1` |
| `{YYYY}` | 4-digit year | `2020` |
| `{JJJ}` | 3-digit zero-padded Julian day | `080` |
| `{hh}` `{mm}` `{ss}` | 2-digit zero-padded UTC hour, minute, second | `00` `30` `59` |
| `{ext}` | file extension from `raw_format` | `msd` |
| `{product}` | output product name (`psd`, `pdf`, `quality`, ...) | `psd` |

- Raw data is discovered with `raw_file_glob` (wildcards for the start time), because the start time of the first file can differ by station. Parse the actual start time from the file name or header, never assume it.

## 2. Time

- All times are UTC.
- In files, times are written as ISO 8601 strings: `2020-03-20T00:30:59Z`.
- Where a numeric "serial" time is needed (station table on/off dates, data-status CSV), it is **days since 1970-01-01T00:00:00Z** as a double. This is not MATLAB `datenum` and not Python `date.toordinal()`.
- Conversions to remember:
  - MATLAB: `datenum` of the Unix epoch is 719529, so `serial = datenum(t) - 719529`.
  - Python: `serial = (t - datetime(1970,1,1,tzinfo=utc)).total_seconds() / 86400`.
  - (For reference, MATLAB `datenum` equals Python `toordinal()` plus 366.)
- A cross-language test must confirm that both parse the same timestamp to the same serial value.

## 3. Channels

- Channel codes differ between deployments. The `channels` block in the config maps each code to a role: `pressure`, `vertical`, `H1`, `H2` (or `north`, `east` for the NE scheme).
- Code never branches on a channel code like `BH1`. It looks up the role.
- Per-role settings (PSD thresholds, response output units) are keyed by role.
- Open item: which of CH0-CH3 is which role has not been recorded. Leave the `CH` scheme entries as `null` until confirmed from the instrument metadata.

## 4. File formats

| Product | Format | Notes |
|---|---|---|
| Station table | CSV | one row per station |
| Orientation file | CSV | station, lat, lon, H1 azimuth, H2 azimuth, 2-sigma error |
| Quality matrix and data-status | CSV | cells use quality codes from the config (NaN no data, 0 bad, 1 low PSD, 2 good) |
| PSDs, PDFs, spectrogram arrays | NetCDF4 | named dimensions, units attribute on every variable |
| Waveforms | miniSEED or SAC | read by ObsPy in Python and a reader of the team's choice in MATLAB |
| Event catalog | CSV | origin time as ISO string, lat, lon, depth_km, magnitude |

Rules:
- CSV: UTF-8, comma-delimited, one header row, snake_case column names, missing value is an empty cell, booleans are `1` or `0`.
- NetCDF: always read and write variables by **dimension name**, never by position. MATLAB's `ncread` typically returns dimensions in the reverse order from how Python (xarray) lists them, so any code that assumes position will silently transpose. A cross-language test must check this.
- Do not use pickle or MATLAB `.mat` files for anything shared.
- Every NetCDF output has these global attributes: `lobster_version`, `written_by` (`python` or `matlab`), `written_at` (ISO UTC), and `config_json` (the full text of the config used).

## 5. Station table columns

Provider-given and derived columns are kept together in one CSV but are separated by this table so that rerunning the pipeline knows what it may overwrite. Derived columns are regenerated whenever thresholds or methods change; provider columns are never overwritten by processing.

| Column | Type | Source |
|---|---|---|
| station | string | provider |
| network | string | provider |
| first_day, last_day | ISO date | provider |
| latitude, longitude | degrees | provider |
| depth_m | meters, positive down | provider |
| sensor_type | string (for example ANT240) | provider |
| instrument_name | string | provider |
| channel_names | semicolon-separated string | provider |
| resp_path_{role} | string | derived from config pattern |
| pzfile_path_{role} | string | derived from config pattern |
| h1_azimuth_deg, h2_azimuth_deg | degrees clockwise from north | derived |
| orientation_2sigma_deg | degrees | derived |
| on_date, off_date | serial days | provider |
| deployment_duration_days | days | derived |
| good_data_pct_{role} | percent | derived |
| valid_timing | 1/0 | derived |
| differential_sensor | 1/0 (differential vs absolute) | provider |
| drift_rate_ms_per_day | ms/day | derived |
| timing_method | `clock` or `ancc` | derived |
| logger_status | 1/0 | provider |
| main_battery | 1/0 | provider |
| data_saved | 1/0 | provider |

Open item: the notes list "Orientation 2 std error" and "Good Data % on Channel 1-N". Confirm whether one value or one per channel is wanted.

## 6. Conventions that must match

- **Azimuth**: degrees clockwise from north, 0 to 360. H1 azimuth is the azimuth of the H1 horizontal; H2 is H1 + 90 for a right-handed set unless the table says otherwise.
- **PSD units**: dB relative to (unit of response-removed output)^2/Hz, with the unit recorded in the NetCDF `units` attribute. Pressure and seismic channels have different units, so thresholds are per role.
- **Response removal**: the reference definition is: remove instrument response from the RESP file (including the FIR stage) to the output units in the config. Python uses `remove_response`; MATLAB must reproduce the same transfer function. A cross-language test compares the response at fixed frequencies.
- **Indexing**: never write indices to files. Dates, station codes and frequencies identify rows.
- **Hourly PSDs are the primitive.** Daily statistics are derived from them so that daily quality thresholds and ATaCR's hourly selection share one data product.

## 7. Config field reference

| Field | Meaning |
|---|---|
| `lobster_config_version` | version of this config schema |
| `experiment.name`, `network`, `stations` | label, network code, station codes to process |
| `paths.*` | directory and file locations; `{root}` and other keys are substituted |
| `file_conventions.raw_format` | `msd`, `mseed` or `sac`; sets `{ext}` and reader choice |
| `file_conventions.raw_files_per` | `day` or `hour` (open question for the demo dataset) |
| `file_conventions.raw_file_glob` | pattern used to find raw files for one station-channel-day |
| `file_conventions.raw_file_pattern` | full pattern, used for parsing start times |
| `file_conventions.resp_file_pattern`, `pzfile_pattern` | where response files live |
| `file_conventions.output_pattern_station_channel` | where per-station-channel outputs go |
| `channels.scheme_in_use` | which scheme in `channels.schemes` applies to this experiment |
| `channels.schemes.*` | channel code to role map |
| `time.*` | time conventions (fixed; stated here so scripts can assert them) |
| `quality.codes` | the values used in quality matrices |
| `quality.psd.*` | PSD window length and thresholds, per role |
| `response.output_units` | units after response removal, per role (`VEL`, `DISP`, `ACC`, or `PA` for pressure) |
| `response.filter_fir_response` | include FIR stage in response removal |
| `orientation.*` | method name and event-selection limits |
| `atacr.required`, `min_obstools_version` | settings for the ATaCR input check |

## 8. ATaCR

ATaCR is not wrapped. `atacr_checks/` contains:
- an input check that resolves the ATaCR data, spectra, transfer-function and quality-matrix paths from the config and confirms they exist and follow ATaCR's expected layout,
- a smoke test that runs ATaCR on a short span of the test dataset,
- a version report (OBStools, ObsPy, Python).

Its output is a plain-text report so the MATLAB workflow can use it without touching Python.

## 9. Ownership of each step

Each step has one canonical implementation; the other language ports it and tests against it. Fill this in as steps are claimed.

| Step | Canonical | Port | Cross-language test |
|---|---|---|---|
| Config + path resolution | | | |
| Station table | | | |
| Response removal | | | |
| Timing corrections | | | |
| Hourly/daily PSD + quality matrix | | | |
| Spectrograms | | | |
| PDFs of PSDs | | | |
| Orientation | | | |
| Demo products | | | |

## 10. Cross-language tests (`tests_crosslang/`)

1. Both languages resolve the same file paths for every station, channel and day in the test dataset.
2. Both parse the same timestamp to the same serial value.
3. Both compute the instrument response from the same RESP file at fixed frequencies and agree within tolerance.
4. Python writes hourly PSDs, MATLAB reads them by dimension name and compares to its own result (and the reverse). Compare with numerical tolerances, not exact equality.
5. Both read the same config and the same CSV quality matrix and agree on the count of good, bad and no-data cells.