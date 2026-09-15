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

## Development

```bash
python -m pip install -e .
streamlit run app/main.py
```

Run tests with:

```bash
pytest
```

## Project status

- [x] Project configuration model
- [x] Validation and resolution semantics
- [x] Streamlit configuration UI
- [x] Project manifest export
- [ ] DEM acquisition and terrain processing
- [ ] weather/climate data adapters
- [ ] hydrologic flow and recharge engine
- [ ] geology / wells / springs adapters
- [ ] MODFLOW 6 / FloPy integration
- [ ] candidate-zone ranking
- [ ] 3D terrain and video pipeline

## References

- USGS MODFLOW 6: https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model
- USGS MODFLOW 6 GWF documentation: https://www.usgs.gov/publications/documentation-modflow-6-groundwater-flow-model
- pywatershed: https://github.com/DOI-USGS/pywatershed
