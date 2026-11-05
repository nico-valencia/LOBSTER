# Nov 4 2026	OBS Data Preprocessing Meeting 

### DEMO OBS DATASET - raw data file convention in .msd format 

```
…/ORCA/DemoORCA/MM04.CH1.2020.080.00.30.59.msd
…/main_repo/data_repo/station.channelcode.year.julianday.hour.minute.second.msd
```

- 1 file per day (or hour?) per channel, starting at 30 min 59 sec for MM04
- Potentially different number of files or starting time at different stations 
- All in UTC format 

### DEMO OBS DATASET - response files 

```
.../ORCA/PacORCA_database/RESP/RESPfiles/CH1/RESP.XX.MM04..CH1
.../main_repo/metadata_repo/response_repo/response_files/channelcode/RESP.network.station..channelcode
```

- Response files are given per channel, with each station in folder
- SEED type response file (both SEED format and human readable)
- given `grab_RESP_from_ORCA.m`, poles and zeros per channel, and sensitivity 

- metafile for response necessary to association channel with direction (within miniseed header)

- Channel Stages: 
    - CH 0/1/2/3 :  one pressure channel and three seismic channels
    - BDH, BHZ/1/2 : pressure gauge, vertical and two horizontals
    - BDH, BHZ/N/E : pressure gauge, vertical, north, and east

- response files are small so we can reproduce them for each Stage, potentially 1/2 --> N/E stages may have same horizontal response! (and we can write a test for this...)

- response depends on seismometer used (nanometrics, trillium) so be sure to be careful with this

#### Response Files - pzfiles

```
.../ORCA/PacOrca_database/RESP/pzfiles/BH1/RESP.XX.MM04..BH1
.../main_repo/metadata_repo/response_repo/pzfiles/channelcode/RESP.network.station..channelcode
```
And each of these files looks like this: 

```
1459730000.0
0.2
3.38073468e+18
4
7
0j 0j -108+0j -161+0j
-0.01815+0.01799j -0.01815-0.01799j -173+0j -196+231j -196-231j -732+1415j -732-1415j
```

pzfiles have gain, sensitivity, some other value, # of zeroes, # of poles, values of zeroes, values of poles

## GOALS 

`PacORCA_database/` is the target!! This is a template for the workflow we are making...

**Deliverable 1**: File with all station metadata, *which will be a supp info file for data paper and used all the time for our research problems...*

File Structure: 

```
Station Code
Network
First Day and Last Day of Data Acquisition
Latitude / Longitude / Depth
Sensor Type (ex: ANT240 is an Angler style OBS with a Trillium 240 seismometer)
Instrument Name (will come from instrument provider)
Channel Names (CH0/1/2/3 & BDH/1/2/Z)
RESP filepaths (for all channels)
pzfiles fileoaths (for all channels)
Orientation (H1 & H2 azimuths)
Orientation 2 std error 
On/Off Date in Serial Time 
Deployment Duration
Good Data % on Channel 1-N
Validtiming? (bool)
Diff Sensor? (bool, differential vs absolute measurement)
Drift Rate (ms/day)
Timing Method (clock or ANCC)
Loggerstatus (bool)
Main Battery (bool)
Data Saved? (bool)
```

	
ALL FILES TXT OR CSV FORMAT 
Orientation_file : repeat station lat lon and orientations 

Data_status plot : green is good, red is data but bad, black is no data 
	Also come with csv (USEFUL FOR ME AND JESS)
		Serial day and datestring 
		Station_channel
Cells: Nan for no data, 0 for bad, 1 for low PSD stuff , 2 for good  
	
There are some code overlaps with ATaCR and this workflow: it calculates hourly PSDs to find the ambient background data WITHOUT EQ recordings

Lun has thresholds for daily PSDs to determine good or bad days for data quality 

Zach has an outlier check for PSDs vs absolute 

3 kinds of hours: useless data and PSD is trash 
			Doesnt look like neighbors but is a seismic 
			Looks like neighbors and is good background noise 

	Makes sense to cross reference ATaCR

front end culling for all days and channels , if passes then ATaCR can look at it later 
Should make PSD stacks to convince myself of the thresholds

Analysis stuff 
	Ideally, this is PUBLISHED WITH A GITHUB REPO AND ITS USABLE BY MANY 
	Parameters file or folder for everything, make this not experiment specific
	
demostuff 
	List of earthquakes: go through list and plot waveforms of the eq at that time
	Just press play and produce a record section, multistation or single station
	Clock corrections
	T phases 
	Every single station has a spectrogram 



Code Goals: 
modular code for either mseed or seed or sac file format → use obspy tools to determine reader and then read codes properly

Have both functionalities for corrected tilt / compliance within the workflow (for eq data)
