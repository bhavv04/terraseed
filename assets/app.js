const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

const MONTH_FULL = [
  'January', 'February', 'March', 'April',
  'May', 'June', 'July', 'August',
  'September', 'October', 'November', 'December'
];

const VEG_WEIGHTS = {
  reforestation: {
    temp: 0.30,
    precip: 0.30,
    frost: 0.20,
    soil: 0.20,
  },

  crops: {
    temp: 0.30,
    precip: 0.25,
    frost: 0.15,
    soil: 0.30,
  },

  shrubs: {
    temp: 0.25,
    precip: 0.25,
    frost: 0.25,
    soil: 0.25,
  },

  grassland: {
    temp: 0.28,
    precip: 0.28,
    frost: 0.22,
    soil: 0.22,
  },
};

const VEG_LABELS = {
  reforestation: 'Reforestation',
  crops: 'Crops',
  shrubs: 'Native shrubs',
  grassland: 'Grassland',
};

let climateData = null;
let currentVeg = 'reforestation';
let mapPinAdded = false;

/* LOAD DATA */

fetch('assets/climate_data.json')
  .then(response => response.json())
  .then(data => {
    climateData = data;
    renderMap();
  });

/* VEG SELECTION */

function selectVeg(element) {
  document.querySelectorAll('.veg-chip').forEach(chip => {
    chip.classList.remove('active');
  });

  element.classList.add('active');
  currentVeg = element.dataset.veg;
}

/* SCORING */

function scoreTemp(temp) {
  if (temp === null || isNaN(temp)) return 0;

  if (temp < 0) return 0;

  if (temp < 10) {
    return (temp / 10) * 60;
  }

  if (temp <= 25) {
    return 100;
  }

  if (temp <= 35) {
    return ((35 - temp) / 10) * 100;
  }

  return 0;
}

function scorePrecip(precip) {
  if (precip === null || isNaN(precip)) return 0;

  if (precip < 10) return 0;

  if (precip < 50) {
    return (precip / 50) * 80;
  }

  if (precip <= 150) {
    return 100;
  }

  if (precip <= 300) {
    return ((300 - precip) / 150) * 100;
  }

  return 20;
}

function scoreFrost(temp) {
  if (temp === null || isNaN(temp)) return 0;

  if (temp < -5) return 0;

  if (temp < 5) {
    return ((temp + 5) / 10) * 60;
  }

  return 100;
}

function scoreSoil(soil) {
  if (soil === null || isNaN(soil)) return 0;

  if (soil < 0.05) return 0;

  if (soil < 0.2) {
    return (soil / 0.2) * 70;
  }

  if (soil <= 0.4) {
    return 100;
  }

  if (soil <= 0.6) {
    return ((0.6 - soil) / 0.2) * 80;
  }

  return 20;
}

/* SCORE CALCULATIONS */

function getScores(latIdx, lonIdx, veg) {
  const weights = VEG_WEIGHTS[veg];

  return MONTH_NAMES.map((_, monthIndex) => {
    const temp = climateData.t[monthIndex][latIdx][lonIdx];
    const precip = climateData.p[monthIndex][latIdx][lonIdx];
    const soil = climateData.s[monthIndex][latIdx][lonIdx];

    if (temp === null || precip === null || soil === null) {
      return 0;
    }

    const tempScore = scoreTemp(temp);
    const precipScore = scorePrecip(precip);
    const frostScore = scoreFrost(temp);
    const soilScore = scoreSoil(soil);

    const finalScore =
      (weights.temp * tempScore) +
      (weights.precip * precipScore) +
      (weights.frost * frostScore) +
      (weights.soil * soilScore);

    return Math.round(finalScore * 10) / 10;
  });
}

function getAnnualMean(veg) {
  const lats = climateData.lats;
  const lons = climateData.lons;

  return lats.map((_, latIndex) => {
    return lons.map((__, lonIndex) => {
      const scores = getScores(latIndex, lonIndex, veg);

      const validScores = scores.filter(score => score > 0);

      if (!validScores.length) {
        return null;
      }

      const average =
        validScores.reduce((a, b) => a + b, 0) /
        validScores.length;

      return Math.round(average * 10) / 10;
    });
  });
}

/* MAP */

function renderMap() {
  const lats = climateData.lats;
  const lons = climateData.lons;

  const z = getAnnualMean(currentVeg);

  Plotly.newPlot(
    'world-map',
    [
      {
        type: 'heatmap',

        z,
        x: lons,
        y: lats,

        zmin: 0,
        zmax: 100,

        colorscale: [
          [0.0, '#f5ede0'],
          [0.25, '#d4b896'],
          [0.5, '#c4d4b0'],
          [0.75, '#7a9e6e'],
          [1.0, '#3d6b35'],
        ],

        hoverongaps: false,

        hovertemplate: 'Score: %{z:.1f}<extra></extra>',

        colorbar: {
          thickness: 8,
          len: 0.7,
          outlinewidth: 0,

          tickfont: {
            size: 10,
            color: '#8a8070',
          },
        },
      },
    ],
    {
      margin: {
        l: 0,
        r: 0,
        t: 0,
        b: 0,
      },

      paper_bgcolor: 'white',
      plot_bgcolor: '#dde8f0',

      dragmode: false,

      xaxis: {
        showgrid: false,
        zeroline: false,
        showticklabels: false,
      },

      yaxis: {
        showgrid: false,
        zeroline: false,
        showticklabels: false,
      },
    },
    {
      responsive: true,
      displayModeBar: false,
    }
  );

  mapPinAdded = false;
}

function addMapPin(lat, lon) {
  const displayLon = lon < 0 ? lon + 360 : lon;

  if (mapPinAdded) {
    Plotly.deleteTraces('world-map', [1]);
  }

  Plotly.addTraces('world-map', [
    {
      type: 'scatter',

      x: [displayLon],
      y: [lat],

      mode: 'markers',

      marker: {
        size: 16,
        color: '#3d2b1f',

        line: {
          color: 'white',
          width: 2.5,
        },
      },

      showlegend: false,
      hoverinfo: 'skip',
    },
  ]);

  mapPinAdded = true;
}

/* POLAR CHART */

function renderPolarChart(scores) {
  const fullScores = [...scores, scores[0]];
  const fullMonths = [...MONTH_NAMES, MONTH_NAMES[0]];

  const colors = scores.map(score => {
    if (score >= 70) return '#4a6741';
    if (score >= 40) return '#c8962e';

    return '#a0522d';
  });

  Plotly.newPlot(
    'polar-chart',
    [
      {
        type: 'scatterpolar',

        r: fullScores,
        theta: fullMonths,

        fill: 'toself',
        fillcolor: 'rgba(74,103,65,0.12)',

        line: {
          color: '#4a6741',
          width: 2,
        },

        mode: 'lines',

        hovertemplate: '%{theta}: %{r:.1f}<extra></extra>',
      },

      {
        type: 'scatterpolar',

        r: scores,
        theta: MONTH_NAMES,

        mode: 'markers',

        marker: {
          color: colors,
          size: 10,

          line: {
            color: 'white',
            width: 2,
          },
        },

        hovertemplate: '%{theta}: %{r:.1f}<extra></extra>',

        showlegend: false,
      },
    ],
    {
      paper_bgcolor: 'white',
      showlegend: false,

      margin: {
        l: 48,
        r: 48,
        t: 32,
        b: 32,
      },

      polar: {
        bgcolor: '#fafaf7',

        radialaxis: {
          visible: true,
          range: [0, 100],

          tickvals: [25, 50, 75, 100],

          gridcolor: '#ede7d9',
          linecolor: '#ede7d9',

          tickfont: {
            size: 9,
            color: '#8a8070',
          },
        },

        angularaxis: {
          gridcolor: '#ede7d9',
          linecolor: '#ede7d9',

          tickfont: {
            size: 11,
            color: '#3d2b1f',
          },
        },
      },
    },
    {
      responsive: true,
      displayModeBar: false,
    }
  );
}

/* VEG INFO */

function renderVegWeights(veg) {
  const weights = VEG_WEIGHTS[veg];

  const labels = {
    temp: 'Temperature',
    precip: 'Rainfall',
    frost: 'Frost risk',
    soil: 'Soil moisture',
  };

  document.getElementById('veg-weights').innerHTML =
    Object.entries(weights)
      .map(([key, value]) => {
        return `
          <div class="weight-row">
            <span class="weight-label">${labels[key]}</span>

            <div class="weight-bar-bg">
              <div
                class="weight-bar"
                style="width:${value * 100}%"
              ></div>
            </div>

            <span class="weight-pct">
              ${Math.round(value * 100)}%
            </span>
          </div>
        `;
      })
      .join('');

  document.getElementById('veg-name').textContent =
    VEG_LABELS[veg];
}

/* ANALYSIS */

async function analyze() {
  const cityInput = document.getElementById('city-input');

  const city = cityInput.value.trim();

  if (!city || !climateData) {
    return;
  }

  document.getElementById('geocode-result').textContent =
    'Searching...';

  document.getElementById('loading')
    .classList.add('active');

  document.getElementById('results')
    .classList.add('results-hidden');

  const url =
    `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(city)}&format=json&limit=1`;

  const response = await fetch(url, {
    headers: {
      'Accept-Language': 'en',
    },
  });

  const data = await response.json();

  if (!data.length) {
    document.getElementById('geocode-result').textContent =
      'Location not found. Try a different name.';

    document.getElementById('loading')
      .classList.remove('active');

    return;
  }

  const lat = parseFloat(data[0].lat);
  const lon = parseFloat(data[0].lon);

  const address = data[0].display_name;

  const shortAddress =
    address
      .split(',')
      .slice(0, 2)
      .join(',')
      .trim();

  document.getElementById('geocode-result').textContent =
    `Found: ${address}`;

  /* FIND GRID CELL */

  const lats = climateData.lats;
  const lons = climateData.lons;

  const adjustedLon = lon < 0 ? lon + 360 : lon;

  const latIdx = lats.reduce((bestIndex, value, index) => {
    return Math.abs(value - lat) <
      Math.abs(lats[bestIndex] - lat)
      ? index
      : bestIndex;
  }, 0);

  const lonIdx = lons.reduce((bestIndex, value, index) => {
    return Math.abs(value - adjustedLon) <
      Math.abs(lons[bestIndex] - adjustedLon)
      ? index
      : bestIndex;
  }, 0);

  /* SCORES */

  const scores = getScores(
    latIdx,
    lonIdx,
    currentVeg
  );

  const annual =
    Math.round(
      (scores.reduce((a, b) => a + b, 0) / 12) * 10
    ) / 10;

  const peak = Math.max(...scores);

  const bestIdx = scores.indexOf(peak);

  const goodMonths =
    scores.filter(score => score >= 70).length;

  /* UPDATE UI */

  document.getElementById('location-name').textContent =
    shortAddress;

  document.getElementById('location-coords').textContent =
    `${lat.toFixed(2)}° ${lat >= 0 ? 'N' : 'S'}, ${Math.abs(lon).toFixed(2)}° ${lon >= 0 ? 'E' : 'W'}`;

  document.getElementById('annual-score').textContent =
    annual;

  document.getElementById('peak-score').textContent =
    Math.round(peak * 10) / 10;

  document.getElementById('best-month').textContent =
    MONTH_NAMES[bestIdx];

  document.getElementById('good-months').textContent =
    goodMonths;

  document.getElementById('best-badge').textContent =
    `✦ Best: ${MONTH_FULL[bestIdx]}`;

  document.getElementById('chart-title').textContent =
    shortAddress;

  document.getElementById('chart-sub').textContent =
    `${VEG_LABELS[currentVeg]} · 12-month planting calendar`;

  renderVegWeights(currentVeg);
  renderPolarChart(scores);
  addMapPin(lat, lon);

  document.getElementById('loading')
    .classList.remove('active');

  document.getElementById('results')
    .classList.remove('results-hidden');

  document.getElementById('results')
    .scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    });
}

/* EVENTS */

document.addEventListener('DOMContentLoaded', () => {
  document
    .getElementById('city-input')
    .addEventListener('keydown', event => {
      if (event.key === 'Enter') {
        analyze();
      }
    });
});