import xarray as xr
import numpy as np
import os

os.makedirs('../data/processed', exist_ok=True)

print("Loading climatologies...")
temp = xr.open_dataset('../data/processed/temp_climatology.nc', engine='netcdf4')
precip = xr.open_dataset('../data/processed/precip_climatology.nc', engine='netcdf4')
soil = xr.open_dataset('../data/processed/soil_climatology.nc', engine='netcdf4')

t = temp['t2m'].values    # (12, 180, 360) — Celsius
p = precip['tp'].values   # (12, 180, 360) — m/s
s = soil['swvl1'].values  # (12, 180, 360) — m³/m³

lats = temp['latitude'].values
lons = temp['longitude'].values

print("Computing planting scores with soil moisture...")

# temperature score
def temp_score(t_c):
    return np.where(t_c < 0, 0,
           np.where(t_c < 10, t_c/10*60,
           np.where(t_c <= 25, 100,
           np.where(t_c <= 35, (35-t_c)/10*100, 0))))

# precipitation score
def precip_score(p_m):
    p_mm = p_m * 1000 * 30
    return np.where(p_mm < 10, 0,
           np.where(p_mm < 50, p_mm/50*80,
           np.where(p_mm <= 150, 100,
           np.where(p_mm <= 300, (300-p_mm)/150*100, 20))))

# frost score
def frost_score(t_c):
    return np.where(t_c < -5, 0,
           np.where(t_c < 5, (t_c+5)/10*60, 100))

# soil moisture score — optimal range 0.2-0.4 m³/m³
def soil_score(s_val):
    return np.where(s_val < 0.05, 0,
           np.where(s_val < 0.2, s_val/0.2*70,
           np.where(s_val <= 0.4, 100,
           np.where(s_val <= 0.6, (0.6-s_val)/0.2*80, 20))))

ts = temp_score(t)
ps = precip_score(p)
fs = frost_score(t)
ss = soil_score(s)

# updated weights including soil moisture
planting_score = 0.30*ts + 0.30*ps + 0.20*fs + 0.20*ss

months = np.arange(1, 13)
score_da = xr.DataArray(
    planting_score,
    dims=['month', 'latitude', 'longitude'],
    coords={'month': months, 'latitude': lats, 'longitude': lons}
)
score_ds = score_da.to_dataset(name='planting_score')
score_ds.to_netcdf('../data/processed/planting_scores.nc')

print("Planting scores saved.")
print(f"Score range: {planting_score.min():.1f} to {planting_score.max():.1f}")
print(f"Global mean score: {planting_score.mean():.1f}")