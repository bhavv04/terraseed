import xarray as xr
import numpy as np
import pandas as pd
import os

os.makedirs('../data/processed', exist_ok=True)

# load both files
print("Loading temperature...")
temp = xr.open_dataset('../data/raw/era5_temperature.nc')
print(temp)

print("\nLoading precipitation...")
precip = xr.open_dataset('../data/raw/era5_precipitation.nc')
print(precip)