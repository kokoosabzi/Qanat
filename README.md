# Qanat

A configurable hydrogeospatial analysis platform for terrain, hydrology, recharge and groundwater investigation workflows.

> **Important:** Qanat produces evidence-based candidate zones and uncertainty estimates. It does not guarantee groundwater, water yield, or excavation safety. Field hydrogeology, geophysics, geological interpretation, existing well/spring data, and professional geotechnical review remain necessary before any physical work.

## Vision

```text
Project Configuration
        |
        v
Data Engine ---- DEM / satellite / rainfall / soil moisture / ET / geology / wells / springs
        |
        +--> Terrain Engine ------ elevation / slope / aspect / hillshade / contours
        |
        +--> Hydrology Engine ---- flow / catchments / drainage / recharge indicators
        |
        +--> Groundwater Engine -- MODFLOW 6 / FloPy / calibrated conceptual models
        |
        v
AI Analysis ---------------------- evidence / ranking / uncertainty / explanations
        |
        v
2D maps / 3D terrain / reports / animation
```

## First implementation

The initial application focuses on a stable, reproducible **project manifest** and configuration UI. Heavy geospatial and groundwater engines are intentionally modular so that raster dependencies and numerical solvers can be added without coupling them to the configuration layer.

### Configurable inputs

- latitude / longitude
- analysis extent: radius, rectangle, or polygon
- source DEM resolution and requested output resolution
- terrain, hydrology, geology, groundwater, weather and existing-feature layers
- historical weather period and forecast options
- analysis modules
- 2D / 3D / report / animation outputs

The default project location is **36.3916139, 57.6854968**, but it is only a default and is fully editable.

## Hydrology and groundwater design

The groundwater engine is designed around **MODFLOW 6**, the current core MODFLOW release from the U.S. Geological Survey, with Python orchestration through FloPy. MODFLOW 6 supports three-dimensional transient groundwater flow and packages for recharge, wells, rivers, drains, evapotranspiration and unsaturated-zone flow.

Hydrologic process simulation can optionally use **pywatershed** where its process representations and data requirements are appropriate.

A key modeling rule is preserved throughout the project: **precipitation is not automatically treated as recharge**. Recharge must account for infiltration, evapotranspiration, soil moisture, runoff, land cover and hydrogeologic properties.

## Setup

The complete installation and execution guide is maintained in:

**[`docs/SETUP.md`](docs/SETUP.md)**

The short version for a clean Python 3.11 environment is:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[geo,groundwater,hydrology,test]"
python -m pytest
python -m streamlit run app/main.py
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip setuptools wheel
py -m pip install -e ".[geo,groundwater,hydrology,test]"
py -m pytest
py -m streamlit run app/main.py
```

The project currently supports Python 3.11 and 3.12 as declared by `pyproject.toml`. The core installation is intentionally lightweight; geospatial, groundwater, hydrology and test dependencies are optional extras.

For Python packaging/virtual-environment guidance, see the Python Packaging User Guide. For Streamlit execution, see the official Streamlit run documentation.

## Development documentation

Before changing the project, an AI agent or developer should read:

```text
docs/AGENT_CONTEXT.md
docs/ARCHITECTURE.md
docs/PROJECT_STATE.md
docs/ROADMAP.md
docs/DECISIONS.md
docs/SETUP.md
```

These files are the persistent project handoff layer so development can continue across sessions without relying on conversation history.

## Project status

- [x] Project configuration model
- [x] Validation and resolution semantics
- [x] Streamlit configuration UI
- [x] Project manifest export
- [x] Persistent agent/project documentation
- [x] Complete local setup/run guide
- [ ] CI baseline
- [ ] DEM acquisition and terrain processing
- [ ] weather/climate data adapters
- [ ] hydrologic flow and recharge engine
- [ ] geology / wells / springs adapters
- [ ] MODFLOW 6 / FloPy integration
- [ ] candidate-zone ranking
- [ ] 3D terrain and video pipeline

## Repository structure

```text
app/                 Streamlit/application entry points
qanat/               Scientific/domain package
  config/            project configuration models
  core/              shared domain services
  terrain/           terrain engine
  hydrology/         hydrology engine
  climate/           weather/climate engine
  hydrogeology/      geology/groundwater evidence
  groundwater/       MODFLOW/FloPy integration
  ranking/           evidence fusion and candidate ranking
  provenance/        source/run lineage
  visualization/     map/3D preparation
data/                local datasets; large data is not committed
projects/            project manifests and run metadata
configs/             versioned configuration presets
docs/                persistent project/agent documentation
tests/               automated tests
scripts/             repeatable developer/data utilities
```

## References

- USGS MODFLOW 6: https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model
- USGS MODFLOW 6 GWF documentation: https://www.usgs.gov/publications/documentation-modflow-6-groundwater-flow-model
- pywatershed: https://github.com/DOI-USGS/pywatershed
