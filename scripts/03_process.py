import xarray as xr
import numpy as np
import pandas as pd
import os

os.makedirs('../data/processed', exist_ok=True)

print("Loading processed files...")
temp = xr.open_dataset('../data/processed/temperature_1deg.nc', engine='netcdf4')
precip = xr.open_dataset('../data/processed/precipitation_1deg.nc', engine='netcdf4')

# convert temperature from Kelvin to Celsius
temp['t2m'] = temp['t2m'] - 273.15

# extract month and compute climatology (average per month across all years)
print("Computing monthly climatology...")
temp_clim = temp.groupby('valid_time.month').mean('valid_time')
precip_clim = precip.groupby('valid_time.month').mean('valid_time')

print(f"Temperature climatology shape: {temp_clim['t2m'].shape}")
print(f"Precipitation climatology shape: {precip_clim['tp'].shape}")

# save climatologies
temp_clim.to_netcdf('../data/processed/temp_climatology.nc')
precip_clim.to_netcdf('../data/processed/precip_climatology.nc')

print("Climatologies saved.")

#Processing for soil moisture
import zipfile
import shutil

print("Extracting soil moisture...")
with zipfile.ZipFile('../data/raw/era5_soilmoisture.nc', 'r') as z:
    print(z.namelist())
    z.extract('data_stream-moda.nc', '../data/raw/soilmoisture_temp/')
shutil.move('../data/raw/soilmoisture_temp/data_stream-moda.nc', '../data/raw/era5_soilmoisture_extracted.nc')
print("Extracted")

print("Loading and downsampling soil moisture...")
import xarray as xr
soil = xr.open_dataset('../data/raw/era5_soilmoisture_extracted.nc', engine='netcdf4')
print(soil)
soil_coarse = soil.coarsen(latitude=10, longitude=10, boundary='trim').mean()
soil_coarse.to_netcdf('../data/processed/soilmoisture_1deg.nc')

print("Computing soil moisture climatology...")
soil_clim = soil_coarse.groupby('valid_time.month').mean('valid_time')
soil_clim.to_netcdf('../data/processed/soil_climatology.nc')
print(f"Soil climatology shape: {soil_clim[list(soil_clim.data_vars)[0]].shape}")
print("Done")