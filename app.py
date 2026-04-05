import xarray as xr
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="terraseed")

def geocode_city(city_name):
    try:
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude, location.address
        return None, None, None
    except:
        return None, None, None

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

def get_location_scores_veg(lat, lon, veg_type):
    lon_idx_val = lon + 360 if lon < 0 else lon
    lat_idx = np.argmin(np.abs(lats - lat))
    lon_idx = np.argmin(np.abs(lons - lon_idx_val))

    t = temp_clim['t2m'].values[:, lat_idx, lon_idx]  # already Celsius
    p = precip_clim['tp'].values[:, lat_idx, lon_idx] * 1000 * 30

    w = VEG_WEIGHTS[veg_type]

    ts = np.where(t < 0, 0,
         np.where(t < 10, t/10*60,
         np.where(t <= 25, 100,
         np.where(t <= 35, (35-t)/10*100, 0))))

    ps = np.where(p < 10, 0,
         np.where(p < 50, p/50*80,
         np.where(p <= 150, 100,
         np.where(p <= 300, (300-p)/150*100, 20))))

    fs = np.where(t < -5, 0,
         np.where(t < 5, (t+5)/10*60, 100))

    return w['temp']*ts + w['precip']*ps + w['frost']*fs

def best_window(monthly_scores):
    best_month = int(np.argmax(monthly_scores))
    return MONTH_NAMES[best_month]

app = Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H1("TarraSeed", style={'margin': '0', 'fontSize': '24px', 'fontWeight': '500'}),
        html.P("Optimal planting windows for any location on Earth",
               style={'margin': '0', 'color': '#666', 'fontSize': '13px'}),
    ], style={'marginBottom': '20px'}),

    html.Div([
        dcc.Input(id='city-input', type='text',
                  placeholder='Enter a city (e.g. Toronto, Nairobi, Berlin...)',
                  style={'marginRight': '8px', 'width': '320px'}),
        dcc.Dropdown(
            id='veg-dropdown',
            options=[
                {'label': 'Reforestation', 'value': 'reforestation'},
                {'label': 'Crops', 'value': 'crops'},
                {'label': 'Native shrubs', 'value': 'shrubs'},
                {'label': 'Grassland', 'value': 'grassland'},
            ],
            value='reforestation',
            clearable=False,
            style={'width': '200px', 'marginRight': '8px', 'display': 'inline-block'}
        ),
        html.Button('Analyze', id='analyze-btn', n_clicks=0),
        html.Div(id='geocode-result',
                 style={'fontSize': '12px', 'color': '#888', 'marginTop': '6px'})
    ], style={'marginBottom': '20px', 'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap', 'gap': '8px'}),

    html.Div([
        html.Div([
            dcc.Graph(id='world-map', style={'height': '420px'})
        ], style={'flex': '2', 'marginRight': '16px'}),

        html.Div([
            html.Div(id='location-label',
                     style={'fontSize': '13px', 'color': '#666', 'marginBottom': '12px'}),
            html.Div(id='best-window-badge', style={'marginBottom': '16px'}),
            dcc.Graph(id='monthly-chart', style={'height': '220px'}),
            html.Div(id='metric-cards'),
        ], style={'flex': '1', 'minWidth': '280px'}),

    ], style={'display': 'flex'}),

], style={'fontFamily': 'sans-serif', 'padding': '24px', 'maxWidth': '1200px', 'margin': '0 auto'})


@app.callback(
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
        z=scores_sub,
        x=lons_sub,
        y=lats_sub,
        colorscale=[
            [0, '#8B0000'], [0.3, '#FF8C00'],
            [0.6, '#9FE1CB'], [1.0, '#1D9E75']
        ],
        zmin=0, zmax=100,
        colorbar=dict(title='Planting Score', thickness=12),
        hoverongaps=False,
    ))

    geocode_msg = ''
    if city and n_clicks > 0:
        lat, lon, address = geocode_city(city)
        if lat and lon:
            display_lon = lon + 360 if lon < 0 else lon
            fig.add_trace(go.Scatter(
                x=[display_lon], y=[lat],
                mode='markers',
                marker=dict(size=12, color='white', line=dict(color='black', width=2)),
                showlegend=False
            ))
            geocode_msg = f"Found: {address}"
        else:
            geocode_msg = "Location not found. Try a different city name."

    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        title='Annual planting score — global',
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        plot_bgcolor='#1a1a2e',
        paper_bgcolor='white',
    )
    return fig, geocode_msg


@app.callback(
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
        margin=dict(l=0, r=0, t=0, b=0)
    )

    if not city or n_clicks == 0:
        return empty_fig, '', 'Enter a city and click Analyze', ''

    lat, lon, address = geocode_city(city)
    if not lat:
        return empty_fig, '', 'Location not found', ''

    monthly = get_location_scores_veg(float(lat), float(lon), veg_type)
    best = best_window(monthly)

    colors = ['#1D9E75' if s >= 70 else '#FAC775' if s >= 40 else '#D85A30'
              for s in monthly]

    fig = go.Figure(go.Bar(
        x=MONTH_NAMES,
        y=[round(float(s), 1) for s in monthly],
        marker_color=colors,
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(range=[0, 100], title='Score'),
        plot_bgcolor='white',
        paper_bgcolor='white',
    )

    veg_label = {
        'reforestation': 'Reforestation',
        'crops': 'Crops',
        'shrubs': 'Native shrubs',
        'grassland': 'Grassland'
    }[veg_type]

    badge = html.Div([
        html.Span('Best window: ', style={'fontSize': '13px', 'color': '#666'}),
        html.Span(best, style={
            'fontSize': '13px', 'fontWeight': '500',
            'background': '#EAF3DE', 'color': '#27500A',
            'padding': '3px 10px', 'borderRadius': '99px',
            'marginRight': '8px'
        }),
        html.Span(veg_label, style={
            'fontSize': '12px',
            'background': '#E6F1FB', 'color': '#0C447C',
            'padding': '3px 10px', 'borderRadius': '99px'
        }),
    ])

    label = f"Location: {address}"
    annual_score = round(float(monthly.mean()), 1)
    peak_score = round(float(monthly.max()), 1)

    cards = html.Div([
        html.Div([
            html.Div([
                html.P('Annual score', style={'fontSize': '11px', 'color': '#888', 'margin': '0 0 3px'}),
                html.P(f'{annual_score}', style={'fontSize': '20px', 'fontWeight': '500', 'margin': '0'}),
            ], style={'background': '#f5f5f5', 'borderRadius': '8px', 'padding': '10px 12px'}),
            html.Div([
                html.P('Peak score', style={'fontSize': '11px', 'color': '#888', 'margin': '0 0 3px'}),
                html.P(f'{peak_score}', style={'fontSize': '20px', 'fontWeight': '500', 'margin': '0'}),
            ], style={'background': '#f5f5f5', 'borderRadius': '8px', 'padding': '10px 12px'}),
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '8px', 'marginTop': '12px'})
    ])

    return fig, badge, label, cards


if __name__ == '__main__':
    app.run(debug=True)