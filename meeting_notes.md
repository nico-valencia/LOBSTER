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

CH1/2 → BH1/2 → BHN/E : these response files are small so feel free to copy and paste to make response files for each ‘stage’

Seismometers are all nanometrics so response for all channels should eb the same (maybe z is different due to gravity…) 

We could even write a test to see if responses are identical after each ‘stage’ → BH and BZ only! 

pzfiles/channel/file

Second response file: gain, sensitivity, num of zeros, num of poles, the zeros, the poles


PacORCA_database : the target!! , template for the workflow we are making… 






File with all the latlons for ORCA
Status table (productible): this will be a supp info file for data paper 
	Station codes, networks 
	Ondate YYYYMMDD and offset 
	Lat lon depth 
	Sensor type: ANT240 (ANgler , Trillium 240) naming convention
	Instrument: organization and instrument name 
	Channels 1-8 
	RESP files pwd 1-8 
	H1 azimuth and H2 azimuth (orientation!)
	2 sigma error on azimuth 
	Serial time on date / offset 
	Deployment duration 
	Data fraction on channel 1-8 
	Validtiming? 
	Diffsensor : differential vs absolute voltage 
	Drift rate for clock (ideally a unit with this) ms / day ? 
	Timing method (clock or ANCC)
	Loggerstatus
	Did it work value? 
	
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
