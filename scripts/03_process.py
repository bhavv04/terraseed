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