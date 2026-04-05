import xarray as xr
import numpy as np
import pandas as pd
import os

os.makedirs('../data/processed', exist_ok=True)

print("Loading climatologies...")
temp = xr.open_dataset('../data/processed/temp_climatology.nc', engine='netcdf4')
precip = xr.open_dataset('../data/processed/precip_climatology.nc', engine='netcdf4')

t = temp['t2m'].values    # shape (12, 180, 360)
p = precip['tp'].values   # shape (12, 180, 360)
lats = temp['latitude'].values
lons = temp['longitude'].values

print("Computing planting scores...")

# temperature score — optimal range 10-25°C
def temp_score(t_c):
    score = np.where(t_c < 0, 0,
            np.where(t_c < 10, t_c / 10 * 60,
            np.where(t_c <= 25, 100,
            np.where(t_c <= 35, (35 - t_c) / 10 * 100, 0))))
    return score

# precipitation score — optimal 50-150mm/month
def precip_score(p_m):
    p_mm = p_m * 1000 * 30  # convert m/s to mm/month approx
    score = np.where(p_mm < 10, 0,
            np.where(p_mm < 50, p_mm / 50 * 80,
            np.where(p_mm <= 150, 100,
            np.where(p_mm <= 300, (300 - p_mm) / 150 * 100, 20))))
    return score

# frost risk score — penalize months near freezing
def frost_score(t_c):
    score = np.where(t_c < -5, 0,
            np.where(t_c < 5, (t_c + 5) / 10 * 60,
            100))
    return score

ts = temp_score(t)
ps = precip_score(p)
fs = frost_score(t)

# weighted composite score
planting_score = (0.35 * ts + 0.35 * ps + 0.30 * fs)

# build xarray for saving
months = np.arange(1, 13)
score_da = xr.DataArray(
    planting_score,
    dims=['month', 'latitude', 'longitude'],
    coords={'month': months, 'latitude': lats, 'longitude': lons}
)
score_ds = score_da.to_dataset(name='planting_score')
score_ds.to_netcdf('../data/processed/planting_scores.nc')

print("Planting scores computed and saved.")
print(f"Score range: {planting_score.min():.1f} to {planting_score.max():.1f}")
print(f"Global mean score: {planting_score.mean():.1f}")