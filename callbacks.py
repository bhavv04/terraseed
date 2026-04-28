import numpy as np
import xarray as xr
import plotly.graph_objects as go
from dash import Input, Output, State, html, callback
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="terraseed")

ds = xr.open_dataset('data/processed/planting_scores.nc')
scores = ds['planting_score'].values
lats = ds['latitude'].values
lons = ds['longitude'].values
annual_mean = scores.mean(axis=0)

temp_clim = xr.open_dataset('data/processed/temp_climatology.nc', engine='netcdf4')
precip_clim = xr.open_dataset('data/processed/precip_climatology.nc', engine='netcdf4')

MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun',
               'Jul','Aug','Sep','Oct','Nov','Dec']

VEG_WEIGHTS = {
    'reforestation': {'temp': 0.35, 'precip': 0.35, 'frost': 0.30},
    'crops':         {'temp': 0.40, 'precip': 0.40, 'frost': 0.20},
    'shrubs':        {'temp': 0.30, 'precip': 0.30, 'frost': 0.40},
    'grassland':     {'temp': 0.33, 'precip': 0.34, 'frost': 0.33},
}

VEG_LABELS = {
    'reforestation': 'Reforestation',
    'crops': 'Crops',
    'shrubs': 'Native shrubs',
    'grassland': 'Grassland'
}


def geocode_city(city_name):
    try:
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude, location.address
        return None, None, None
    except:
        return None, None, None


def get_location_scores_veg(lat, lon, veg_type):
    lon_idx_val = lon + 360 if lon < 0 else lon
    lat_idx = np.argmin(np.abs(lats - lat))
    lon_idx = np.argmin(np.abs(lons - lon_idx_val))
    t = temp_clim['t2m'].values[:, lat_idx, lon_idx]
    p = precip_clim['tp'].values[:, lat_idx, lon_idx] * 1000 * 30
    w = VEG_WEIGHTS[veg_type]
    ts = np.where(t < 0, 0, np.where(t < 10, t/10*60,
         np.where(t <= 25, 100, np.where(t <= 35, (35-t)/10*100, 0))))
    ps = np.where(p < 10, 0, np.where(p < 50, p/50*80,
         np.where(p <= 150, 100, np.where(p <= 300, (300-p)/150*100, 20))))
    fs = np.where(t < -5, 0, np.where(t < 5, (t+5)/10*60, 100))
    return w['temp']*ts + w['precip']*ps + w['frost']*fs


def best_window(monthly_scores):
    return MONTH_NAMES[int(np.argmax(monthly_scores))]


def score_color(s):
    if s >= 70: return '#1a7a52'
    if s >= 40: return '#b87120'
    return '#b03a2a'


@callback(
    Output('world-map', 'figure'),
    Output('geocode-result', 'children'),
    Input('analyze-btn', 'n_clicks'),
    State('city-input', 'value'),
)
def update_map(n_clicks, city):
    step = 2
    lats_sub = lats[::step]
    lons_sub = lons[::step]
    scores_sub = annual_mean[::step, ::step]

    fig = go.Figure(go.Heatmap(
        z=scores_sub, x=lons_sub, y=lats_sub,
        colorscale=[
            [0.0,  '#fef2f0'],
            [0.25, '#fdd0c0'],
            [0.5,  '#d4e9c8'],
            [0.75, '#7dc4a0'],
            [1.0,  '#1a7a52'],
        ],
        zmin=0, zmax=100,
        colorbar=dict(
            thickness=8, len=0.7,
            tickfont=dict(size=10, color='#b0b0aa'),
            tickcolor='#e0e0da',
            bordercolor='rgba(0,0,0,0)',
            bgcolor='rgba(0,0,0,0)',
            outlinewidth=0,
        ),
        hoverongaps=False,
    ))

    geocode_msg = ''
    if city and n_clicks > 0:
        lat, lon, address = geocode_city(city)
        if lat and lon:
            display_lon = lon + 360 if lon < 0 else lon
            fig.add_trace(go.Scatter(
                x=[display_lon], y=[lat], mode='markers',
                marker=dict(size=14, color='#1a7a52',
                            line=dict(color='white', width=2.5)),
                showlegend=False,
                hovertext=address,
            ))
            geocode_msg = f"Showing results for {address}"
        else:
            geocode_msg = "Location not found. Try a different city name."

    fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor='white',
        plot_bgcolor='#f0f4f8',
        xaxis=dict(showgrid=False, zeroline=False,
                   showticklabels=False, title=''),
        yaxis=dict(showgrid=False, zeroline=False,
                   showticklabels=False, title=''),
    )
    return fig, geocode_msg


@callback(
    Output('monthly-chart', 'figure'),
    Output('best-window-badge', 'children'),
    Output('location-label', 'children'),
    Output('metric-cards', 'children'),
    Input('analyze-btn', 'n_clicks'),
    State('city-input', 'value'),
    State('veg-dropdown', 'value'),
)
def update_panel(n_clicks, city, veg_type):
    empty_fig = go.Figure()
    empty_fig.update_layout(
        paper_bgcolor='white', plot_bgcolor='white',
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        annotations=[dict(
            text='Search a city above to see the planting calendar',
            x=0.5, y=0.5, xref='paper', yref='paper',
            showarrow=False, font=dict(size=13, color='#c0c0ba'),
        )]
    )

    if not city or n_clicks == 0:
        return empty_fig, '', '', ''

    lat, lon, address = geocode_city(city)
    if not lat:
        return empty_fig, '', 'Location not found', ''

    monthly = get_location_scores_veg(float(lat), float(lon), veg_type)
    best = best_window(monthly)

    bar_colors = ['#1a7a52' if s >= 70 else '#e8a030' if s >= 40 else '#e05535'
                  for s in monthly]

    fig = go.Figure(go.Bar(
        x=MONTH_NAMES,
        y=[round(float(s), 1) for s in monthly],
        marker_color=bar_colors,
        marker_line_width=0,
        hovertemplate='%{x}: %{y}<extra></extra>',
    ))
    fig.update_layout(
        margin=dict(l=20, r=20, t=16, b=20),
        yaxis=dict(range=[0, 100], showgrid=True,
                   gridcolor='#f0f0eb', tickfont=dict(size=10, color='#b0b0aa'),
                   zeroline=False, title=''),
        xaxis=dict(tickfont=dict(size=11, color='#6b6b65'), showgrid=False),
        plot_bgcolor='white',
        paper_bgcolor='white',
        bargap=0.3,
    )

    badge = html.Div([
        html.Span(f"✦ Best: {best}", className='badge-green'),
        html.Span(VEG_LABELS[veg_type], className='badge-gray'),
    ])

    short_address = address.split(',')[0] + ', ' + address.split(',')[-1].strip()
    annual_score = round(float(monthly.mean()), 1)
    peak_score = round(float(monthly.max()), 1)

    cards = html.Div([
        html.Div([
            html.P('Annual score', className='metric-label'),
            html.P(f'{annual_score}', className='metric-value',
                   style={'color': score_color(annual_score)}),
            html.P('out of 100', className='metric-sub'),
        ], className='metric-card'),

        html.Div([
            html.P('Peak score', className='metric-label'),
            html.P(f'{peak_score}', className='metric-value',
                   style={'color': score_color(peak_score)}),
            html.P('out of 100', className='metric-sub'),
        ], className='metric-card'),

        html.Div([
            html.P('Best month', className='metric-label'),
            html.P(best, className='metric-value',
                   style={'color': '#1a7a52'}),
            html.P('to plant', className='metric-sub'),
        ], className='metric-card'),

        html.Div([
            html.P('Vegetation', className='metric-label'),
            html.P(VEG_LABELS[veg_type], className='metric-value',
                   style={'color': '#1a1a18', 'fontSize': '18px'}),
        ], className='metric-card'),

    ])

    return fig, badge, short_address, cards