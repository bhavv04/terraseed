import cdsapi
import os

os.makedirs('../data/raw', exist_ok=True)

c = cdsapi.Client()

# download monthly mean temperature 1990-2020
c.retrieve(
    'reanalysis-era5-land-monthly-means',
    {
        'product_type': 'monthly_averaged_reanalysis',
        'variable': '2m_temperature',
        'year': [str(y) for y in range(1990, 2021)],
        'month': [f'{m:02d}' for m in range(1, 13)],
        'time': '00:00',
        'format': 'netcdf',
    },
    '../data/raw/era5_temperature.nc'
)

print("Temperature downloaded")

# download monthly total precipitation
c.retrieve(
    'reanalysis-era5-land-monthly-means',
    {
        'product_type': 'monthly_averaged_reanalysis',
        'variable': 'total_precipitation',
        'year': [str(y) for y in range(1990, 2021)],
        'month': [f'{m:02d}' for m in range(1, 13)],
        'time': '00:00',
        'format': 'netcdf',
    },
    '../data/raw/era5_precipitation.nc'
)

print("Precipitation downloaded")
print("All done")