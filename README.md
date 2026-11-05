# OBSqcpp

## Ocean Bottom Seismometer quality control & pre processing 

WIP for analysis of raw data from OBS. 

Outline of how code will work: 

1. Determine if data is in `.msd` or `.SAC` format. 

2. Per station and channel, apply instrument response and FIR filter response from `RESPFILES/` using either `obspy.simulate()` or `obspy.remove_response()`. 

3. Calculate daily power spectral densty (PSD) per station and channel [ideally parallelized], and calculate thresholds for normal PSD vs anomalous PSD. 
    * **Figure**: Daily PSD stack per station, median station PSD stack, PSD outlier check (Lun's absolute PSD value vs Zach's relative to median PSD value) 

4. Cull data based on daily quality, save to "data quality matrix" of size *number of stations* X *UTC date* 
    * **Figure**: Graphical displaying amount of "good" vs "bad" data per channel per station over the deployment duration (based on Lun's PSD overview figures)

5. Produce psuedo spectrograms per day per channel for each station. 
    * **Figure**: Per station spectrograms. 

6. Produce Probability Density Function (PDF) of PSDs per channel per station [ideally parallelized], and calculate thresholds for normal PDFs vs anomalous PDFs. 
   Once again, cull data based on thresholds and save to "PDF quality matrix", dimension sizes to be determined...
    * **Figure**: PDF per station for all channels. (similar plots found in PacificORCA data paper and SuppInfo 3/4.)

7. ATaCR for oceanic noise removal. This will be a requirement for users for this package, and we can setup a `check_ATaCR_filepaths()` function or code to make filepaths to the different data, response files, compliance files, and data quality matrix exist and can be used. (another test script...)
    * will require scripts to find clean hourly data on good days without seismic data
    * **Figure**: Example of oceanic noise removal on trace of choice. (similar to ORCA data paper figure)

8. Calculate station orientations, using Rayleigh wave method (?). 
    * catalog of seismic events to use for this (nominal magnitude, epicentral distance, good azimuthal spread(?))
    * **Figure**: orientation calculation gridsearch and traces (Jess has code for this already)

9. DEMO DATA PRODUCTS FROM THE RAW OBS DATA
    * **Figure**: create a record section for an earthquake / catalog of earthquakes
    * **Figure**: previous examples of spectrogram stacks, data quality matrix in plot form, oceanic noise removal examples
    * **Figure**: differential travel time stacks (similar to what is shown in ORCA paper)

    
