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

7. 


random text I wrote 
    random text I have a tab over to the right 

test again 

