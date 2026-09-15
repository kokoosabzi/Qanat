# Qanat

A configurable hydrogeospatial analysis platform for terrain, hydrology, recharge screening and future groundwater investigation workflows.

> **Important:** Qanat produces evidence-based screening indicators and candidate zones. It does not guarantee groundwater, water yield, or excavation safety. Field hydrogeology, geophysics, geological interpretation, well/spring data and professional review remain necessary before physical work.

## Stable milestone: Qanat 0.1.0

The repository is being stabilized around branch:

```text
stable/0.1.0
```

This milestone is intentionally bounded. It delivers a reproducible terrain → hydrology → historical climate workflow that can be run from the Streamlit application and tested without network access through deterministic fixtures.

### Included

- Project configuration and validation
- Streamlit configuration and execution UI
- Copernicus GLO-30 DEM acquisition
- Multi-tile DEM selection/mosaicking
- Local metric reprojection and exact extent clipping
- Elevation, slope, aspect and hillshade
- Contour GeoJSON and terrain provenance
- Deterministic D8 flow direction and accumulation
- Drainage mask and WGS84 drainage network
- Automatic outlet selection and watershed raster generation
- Strahler stream ordering
- Open-Meteo historical precipitation and ET0 adapter
- Deterministic climate water-balance indicators
- Watershed runoff/recharge-indicator/deficit volume conversion
- Top-level terrain → hydrology → climate orchestration
- Regression tests and GitHub Actions for Python 3.11 and 3.12

## Execution flow

```text
ProjectConfig
    ↓
Copernicus GLO-30
    ↓
Terrain Engine
    ↓
Hydrology Engine
  ├── flow direction
  ├── accumulation
  ├── drainage
  ├── stream order
  └── watershed.tif
    ↓
Open-Meteo historical weather
    ↓
Climate Engine
    ↓
Watershed-scale indicators
```

The Streamlit button **Run terrain + hydrology + climate** executes this path for the current project configuration.

## Installation

See the canonical guide in [`docs/SETUP.md`](docs/SETUP.md).

Windows PowerShell:

```powershell
git clone https://github.com/kokoosabzi/Qanat.git
cd Qanat
git fetch origin
git checkout stable/0.1.0
git pull --ff-only origin stable/0.1.0
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[geo,test]"
python -m pytest -v
python -m streamlit run app/main.py
```

Python 3.11 is also supported.

The live terrain/climate workflow requires internet access for Copernicus and Open-Meteo. The automated tests themselves do not require those external services.

## Default project

```text
Latitude:  36.3916139
Longitude: 57.6854968
Radius:    5000 m
Source DEM: 30 m
Output:     30 m
```

These are editable defaults.

## Stable milestone boundaries

The following are deliberately outside `0.1.0`:

- hydrogeological geology/well/spring/fault evidence ingestion
- MODFLOW 6 / FloPy execution
- calibrated groundwater recharge modeling
- AI evidence fusion and candidate ranking
- forecast comparison workflow
- production 3D/video pipeline
- field validation

The current `recharge_indicator_mm` is a transparent screening proxy, not a calibrated groundwater recharge estimate.

## Persistent project documentation

Before implementation work, read:

```text
docs/AGENT_CONTEXT.md
docs/ARCHITECTURE.md
docs/PROJECT_STATE.md
docs/ROADMAP.md
docs/DECISIONS.md
docs/SETUP.md
```

## Repository structure

```text
app/                 Streamlit entry point
qanat/               scientific/domain package
  config/            project configuration
  terrain/           DEM/terrain engine
  hydrology/         D8 hydrology engine
  climate/           weather/climate engine
  hydrogeology/      future evidence ingestion
  groundwater/       future MODFLOW/FloPy integration
  ranking/           future evidence fusion/ranking
data/                local datasets; large data is not committed
projects/            project manifests and run metadata
docs/                persistent project/agent documentation
tests/               automated tests
```

## Scientific boundary

Qanat is a decision-support and evidence-ranking platform. Groundwater conclusions require appropriate hydrogeological evidence, observations and calibration. Physical excavation requires qualified geological/geotechnical assessment and applicable local requirements.
