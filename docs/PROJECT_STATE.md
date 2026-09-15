# Qanat Project State

Updated: 2026-09-15

## Current Status

The repository contains the application/configuration foundation, a validated Terrain Stage 2 implementation, terrain contour/provenance outputs, a deterministic Hydrology engine with D8 routing/accumulation/watershed/drainage-network/stream-order/outlet selection, and a provider-neutral Climate engine for daily precipitation/ET water-balance indicators. Terrain, hydrology, and climate remain research/engineering implementations and are not production-ready.

## Current Objective

Build a reproducible, configurable terrain-to-hydrogeology pipeline for the default study coordinate while keeping every project setting configurable.

## Default Project Seed

```yaml
latitude: 36.3916139
longitude: 57.6854968
extent:
  mode: radius
  radius_m: 5000
resolution:
  source_dem_m: 30
  output_m: 30
```

This is a starting project configuration, not a fixed site requirement.

## Implemented / Present

- Python project metadata and Streamlit configuration application.
- Persistent architecture/context/roadmap/setup documentation.
- Initial `qanat.terrain` package.
- Copernicus GLO-30 public COG acquisition.
- Signed north/south and east/west tile naming.
- Multi-tile selection for analysis bounds and local mosaicking.
- Local UTM reprojection and configurable output resolution.
- Exact circular radius masking in projected metres.
- Polygon/MultiPolygon extent bounds and exact geometry masking in the target projected CRS.
- Terrain artifacts for elevation, slope, aspect, and hillshade.
- 10 m default contour extraction to WGS84 GeoJSON.
- Machine-readable terrain provenance metadata.
- Deterministic raster D8 flow direction and flow accumulation.
- Thresholded drainage raster and WGS84 drainage-network GeoJSON.
- Outlet-based watershed delineation.
- Automatic outlet selection from maximum valid flow accumulation.
- Strahler stream-order rasterization for thresholded drainage cells.
- Provider-neutral daily Climate engine with precipitation, ET, runoff, infiltration, soil storage, water deficit, and recharge-indicator outputs.
- Climate provenance JSON with explicit model assumptions and scientific boundary.
- Regression coverage for terrain, hydrology, and climate calculations.
- GitHub Actions CI workflow for Python 3.11 and 3.12 test environments.

## Verified

### Automated tests

- Windows Python 3.12.10 virtual environment previously passed the terrain/config suite: 9 passed, 1 warning.
- Hydrology regression coverage includes outlet selection, stream order, watershed delineation, drainage vectorization, and raster outputs.
- Climate regression coverage includes deterministic water balance, missing-ET behavior, water deficit, provenance generation, and invalid-parameter validation.
- A CI run exposed seven earlier implementation/fixture issues; those have been corrected on the branch.
- The Rasterio internal `PendingDeprecationWarning` is not currently treated as a project failure.

### Live Windows terrain run

- `TerrainEngine().run(ProjectConfig())` completed successfully on the target Windows environment before the polygon milestone.
- Output artifacts were created under `data/processed/terrain/`.
- All four baseline terrain artifacts use `EPSG:32640` and 30 m × 30 m resolution.
- DEM dimensions: 338 × 337 pixels.
- DEM valid pixels after nodata masking: 87,258.
- DEM valid elevation range: 1397.6382 m to 2019.3392 m.

## CI Status

- Earlier GitHub Actions failure belonged to `main` commit `14aa21c68e7538e1ae0f3be533a92c316b15bae2`, not the terrain branch.
- The corrected radius-mask expectation is 5 finite pixel centers for the regression fixture.
- The latest known green run before the current hydrology additions was `35014483526` with Python 3.11 and 3.12 jobs successful.
- The latest climate test correction is commit `3c93d32d41904515b24515b5f47d51f9d163b522`; its CI run `35016244027` is currently in progress, so final pass/fail is not yet verified.

## Climate Engine Notes

The climate foundation is intentionally provider-neutral. It accepts daily precipitation and optional ET series and applies explicit assumptions for interception, runoff coefficient, and finite soil-water storage. It reports runoff, infiltration, water deficit, final soil storage, and `recharge_indicator_mm`.

`recharge_indicator_mm` is a screening proxy, not a calibrated groundwater recharge estimate. Reliable recharge modeling still requires appropriate soil, land-cover, ET, geology, storage, and hydrologic calibration, plus validation against observations where available.

## Hydrology Engine Notes

The hydrology foundation uses a strict downhill D8 raster graph. Direction codes follow the common ESRI-style convention: 1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 64=N, 128=NE. Flat cells and local sinks remain direction 0. Flow accumulation is upstream cell count including the cell itself. Drainage is a screening mask based on a configurable accumulation threshold in cells.

Watershed delineation traces all valid upstream cells to a supplied outlet. Automatic outlet selection chooses the valid cell with the greatest flow accumulation, which is a reproducible screening heuristic rather than a guaranteed hydrologic basin outlet.

Stream ordering uses Strahler ordering on thresholded stream cells. This remains a terrain-derived screening layer. Future work should add depression treatment, physically informed precipitation/runoff transformation, watershed-level diagnostics, and optional integration with pywatershed or other physically based components.

## Not Yet Verified

- Full Streamlit application startup on the target Windows machine.
- End-to-end multi-tile processing across a real multi-tile boundary.
- Live polygon extent processing against a downloaded DEM.
- Live contour/provenance generation on the target Windows run.
- Live HydrologyEngine execution against the produced DEM.
- Final passing CI result for the latest climate test correction.
- Live weather/climate provider ingestion and historical/forecast dataset retrieval.
- Hydrogeological evidence ingestion.
- MODFLOW 6 execution.
- Candidate ranking against real data.

## Terrain Engine Notes

The engine uses the public Copernicus GLO-30 COG endpoint and Rasterio/PROJ locally. Copernicus GLO-30 is a DSM, not a bare-earth guarantee; this distinction must remain explicit in scientific reporting. Requested output resolution finer than the source DEM remains resampling, not creation of new terrain information.

Polygon extents are interpreted as GeoJSON Polygon or MultiPolygon geometries in EPSG:4326. Their bounding box determines source-tile acquisition and DEM windowing; exact masking is then performed after reprojection in the local UTM CRS using pixel-center semantics (`all_touched=False`).

## Immediate Next Actions

1. Verify CI for the climate milestone and correct any regressions.
2. Run HydrologyEngine on the real Windows DEM outputs and inspect flow accumulation/network/watershed behavior.
3. Add provider adapters for historical/forecast weather data without coupling them to the water-balance core.
4. Connect climate outputs to watershed-level runoff/recharge indicators.
5. Then move to hydrogeological evidence and groundwater/MODFLOW integration.

## Working Rule

After each meaningful milestone, update this file with what is actually implemented, what was tested, known failures, and exact next actions. Do not mark roadmap items complete based on design discussion alone.
