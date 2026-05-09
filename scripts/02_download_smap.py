import cdsapi
import os

os.makedirs('../data/raw', exist_ok=True)

c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-land-monthly-means',
    {
        'product_type': 'monthly_averaged_reanalysis',
        'variable': 'volumetric_soil_water_layer_1',
        'year': [str(y) for y in range(1990, 2021)],
        'month': [f'{m:02d}' for m in range(1, 13)],
        'time': '00:00',
        'format': 'netcdf',
    },
    '../data/raw/era5_soilmoisture.nc'
)

print("Soil moisture downloaded")