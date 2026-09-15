# Qanat Project State

Updated: 2026-09-15

## Stable milestone

The project is being frozen as **Qanat 0.1.0** on a dedicated stable branch after CI verification. The stable scope is terrain acquisition/processing, deterministic D8 hydrology, automatic watershed generation, historical Open-Meteo climate indicators, and the Streamlit execution path connecting these components.

The implementation remains a research/engineering screening platform and is not a production groundwater model.

## Implemented

- Python project metadata and Streamlit configuration application.
- Persistent architecture/context/roadmap/setup documentation.
- Copernicus GLO-30 public COG acquisition with signed tile naming.
- Multi-tile selection and local mosaicking.
- Local UTM reprojection and configurable output resolution.
- Exact circular radius masking and Polygon/MultiPolygon geometry masking.
- Terrain artifacts: elevation, slope, aspect, hillshade and contours.
- WGS84 contour GeoJSON and machine-readable terrain provenance.
- Deterministic D8 flow direction and flow accumulation.
- Thresholded drainage raster and WGS84 drainage-network GeoJSON.
- Automatic outlet selection from maximum valid accumulation.
- Automatic `watershed.tif` generation from `HydrologyEngine.run()`.
- Strahler stream-order rasterization.
- Provider-neutral daily climate water-balance engine.
- Open-Meteo historical/forecast adapter for precipitation and ET0 normalization.
- Automatic watershed area derivation from projected raster cells.
- Watershed runoff/recharge-indicator/water-deficit conversion from depth to volume.
- `qanat.pipeline.run_hydrology_climate` orchestration for ProjectConfig and legacy DEM callers.
- Streamlit button executing terrain -> hydrology -> historical climate and showing watershed-scale results.
- Regression coverage for terrain, configuration, hydrology, climate, provider normalization, watershed area and end-to-end hydrology-to-climate integration.
- CI matrix for Python 3.11 and 3.12 with package compilation and import smoke tests before pytest.

## Stable verification criteria

Before the `stable/0.1.0` branch is created:

1. Both Python 3.11 and 3.12 CI jobs must pass.
2. Package compilation must pass.
3. `app.main` and `qanat.pipeline` imports must pass.
4. The full pytest suite must pass.
5. Stable documentation must match the actual implemented scope.

The latest CI run before the final freeze had one test failure caused by an incorrect watershed fixture expectation; the fixture has been corrected so a cell draining out of the raster is no longer asserted as upstream of the outlet.

## Live verification status

Previously verified on the target Windows environment:

- `TerrainEngine().run(ProjectConfig())` completed successfully.
- Baseline terrain outputs used EPSG:32640 at 30 m × 30 m.
- DEM dimensions were 338 × 337 pixels.
- Valid DEM pixels were 87,258.
- Elevation range was 1397.6382 m to 2019.3392 m.

Still requires user-side live verification after the stable freeze:

- Full Streamlit startup on the target Windows machine.
- Live Copernicus retrieval and terrain processing from a clean local checkout.
- Live HydrologyEngine execution against the produced DEM.
- Live Open-Meteo retrieval and watershed indicators.
- End-to-end UI execution of the stable branch.

## Climate scientific boundary

The deterministic climate engine estimates runoff, infiltration, soil storage, water deficit and a recharge indicator from provider precipitation/ET0 inputs using explicit parameters. `recharge_indicator_mm` is a screening proxy and is not a calibrated groundwater recharge estimate.

Watershed aggregation assumes the provider point climate series is spatially representative of the watershed. Reliable groundwater recharge modeling requires soil, land cover, ET, geology, storage and hydrologic calibration plus observations where available.

## Hydrology scientific boundary

The hydrology foundation uses a strict downhill D8 raster graph. Automatic outlet selection is a reproducible screening heuristic, not a guaranteed basin outlet. Depression treatment, physically based rainfall-runoff transformation and calibration remain future work.

## Explicitly outside 0.1.0

- Hydrogeological geology/fault/well/spring evidence ingestion.
- MODFLOW 6 / FloPy groundwater execution.
- Calibrated groundwater recharge modeling.
- AI evidence fusion and candidate ranking.
- Forecast comparison workflow.
- Production 3D/video generation.
- Field validation.

## Stable handoff

After the final green CI commit, create `stable/0.1.0` pointing exactly to that commit. The stable branch is the version to clone for local Windows testing. The development branch may continue independently after the freeze.

PR #1 remains open against `main`; this milestone does not require merging the PR.

## Working rule

Do not mark an item verified from design discussion alone. Record exact commits, CI evidence and live-test limitations in this file.
