from dash import dcc, html


def create_layout():
    return html.Div([

        # navbar
        html.Div([
            html.Div([
                html.Span("🌱", className='nav-logo'),
                html.H1("TarraSeed", className='nav-title'),
            ], className='nav-brand'),
            html.Span("Climate Data Science", className='nav-tag'),
        ], className='navbar'),

        # hero
        html.Div([
            html.P("30 years of ERA5 climate data", className='hero-eyebrow'),
            html.H2("Find the best time to plant, anywhere on Earth.",
                    className='hero-title'),
            html.P("TarraSeed scores every location on Earth across 12 months using temperature, precipitation, and frost risk data from ECMWF ERA5.",
                   className='hero-sub'),

            # search bar
            html.Div([
                html.Div([
                    html.Span("🔍", className='search-icon'),
                    dcc.Input(
                        id='city-input',
                        type='text',
                        placeholder='Search a city...',
                    ),
                ], className='search-input-wrap'),

                dcc.Dropdown(
                    id='veg-dropdown',
                    options=[
                        {'label': 'Reforestation', 'value': 'reforestation'},
                        {'label': 'Crops',         'value': 'crops'},
                        {'label': 'Native shrubs', 'value': 'shrubs'},
                        {'label': 'Grassland',     'value': 'grassland'},
                    ],
                    value='reforestation',
                    clearable=False,
                ),

                html.Button('Analyze', id='analyze-btn', n_clicks=0),

            ], className='search-bar'),

            html.Div(id='geocode-result', className='geocode-result'),

        ], className='hero'),

        # main grid
        html.Div([

            # left column
            html.Div([
                # map card
                html.Div([
                    html.Div([
                        html.P("Global planting score", className='card-label'),
                        html.Div(id='best-window-badge'),
                    ], className='card-header'),
                    dcc.Graph(id='world-map', style={'height': '340px'},
                              config={'displayModeBar': False}),
                ], className='card', style={'marginBottom': '20px'}),

                # monthly chart card
                html.Div([
                    html.Div([
                        html.P("Monthly planting score", className='card-label'),
                        html.Div(id='location-label',
                                 className='location-label',
                                 style={'fontSize': '14px', 'fontWeight': '500',
                                        'color': '#6b6b65', 'marginBottom': '0'}),
                    ], className='card-header'),
                    dcc.Graph(id='monthly-chart', style={'height': '200px'},
                              config={'displayModeBar': False}),
                ], className='card'),

            ]),

            # right column
            html.Div([
                html.Div(id='metric-cards'),
            ], className='right-panel'),

        ], className='main-grid'),

    ], className='app-wrapper')