# Qanat Project State

Updated: 2026-09-15

## Current Status

The repository contains the application/configuration foundation, a validated Terrain Stage 2 implementation, terrain contour/provenance outputs, a deterministic Hydrology engine with D8 routing/accumulation/watershed/drainage-network/stream-order/outlet selection, and a provider-backed Climate engine with watershed runoff/recharge indicators. A top-level hydrology-to-climate pipeline now passes the generated watershed raster directly into climate aggregation. Terrain, hydrology, and climate remain research/engineering implementations and are not production-ready.

## Current Objective

Build a reproducible, configurable terrain-to-hydrogeology pipeline for the default study coordinate while keeping every project setting configurable.

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
- Automatic outlet selection from maximum valid flow accumulation, including automatic watershed creation when `HydrologyEngine.run()` receives no explicit outlet.
- Strahler stream-order rasterization for thresholded drainage cells.
- Provider-neutral daily Climate engine with precipitation, ET, runoff, infiltration, soil storage, water deficit, and recharge-indicator outputs.
- Open-Meteo provider adapter for historical/forecast daily precipitation and ET0 data.
- Direct `OpenMeteoProvider -> ClimateEngine` execution path through `ClimateEngine.run_from_provider`.
- Watershed raster area derivation from positive mask cells and pixel transform; no manual watershed area is required when `watershed_raster_path` is supplied.
- Watershed-scale runoff/recharge indicator conversion from depth (mm) to volume (m³) and fractions of precipitation.
- Top-level `qanat.pipeline.run_hydrology_climate` orchestration that runs D8 hydrology, generates/selects the watershed, and feeds its raster directly into climate aggregation.
- Regression coverage for terrain, hydrology, climate calculations, provider normalization, watershed raster area, and the hydrology-to-climate integration using a real generated watershed raster and a deterministic fake provider.
- GitHub Actions CI workflow for Python 3.11 and 3.12 test environments.

## Verified

### Automated tests

- Windows Python 3.12.10 virtual environment previously passed the terrain/config suite: 9 passed, 1 warning.
- Hydrology regression coverage includes outlet selection, stream order, watershed delineation, drainage vectorization, and raster outputs.
- Climate regression coverage includes deterministic water balance, missing-ET behavior, water deficit, provenance generation, provider normalization, watershed area derivation, and provider-to-watershed integration.
- A new end-to-end regression test covers `HydrologyEngine.run() -> watershed.tif -> ClimateEngine.run_from_provider()` through `qanat.pipeline.run_hydrology_climate` without network access.
- The latest CI workflow for the current integration commit has not yet been reported by GitHub and therefore is not marked green.
- The Rasterio internal `PendingDeprecationWarning` is not currently treated as a project failure.

### Live Windows terrain run

- `TerrainEngine().run(ProjectConfig())` completed successfully on the target Windows environment before the polygon milestone.
- Output artifacts were created under `data/processed/terrain/`.
- All four baseline terrain artifacts use `EPSG:32640` and 30 m × 30 m resolution.
- DEM dimensions: 338 × 337 pixels.
- DEM valid pixels after nodata masking: 87,258.
- DEM valid elevation range: 1397.6382 m to 2019.3392 m.

## Climate Engine Notes

`OpenMeteoProvider` normalizes provider responses into `DailyWeather`. `ClimateEngine.run_from_provider` then feeds the normalized daily precipitation and ET0 series into the deterministic water-balance model. The provider layer is replaceable and is not part of the scientific water-balance assumptions.

When a watershed raster is supplied, `watershed_area_from_raster` computes area as positive-cell count multiplied by pixel width × pixel height from the raster transform. This is an exact raster-footprint area in the raster's projected coordinate units; the current implementation is intended for projected metric watershed rasters.

`watershed_indicators` converts runoff, recharge-indicator, and water-deficit depths into watershed volumes. This assumes the provider climate series is spatially representative of the watershed. `recharge_indicator_mm` and its volume equivalent remain screening proxies, not calibrated groundwater recharge estimates.

Reliable recharge modeling still requires appropriate soil, land-cover, ET, geology, storage, and hydrologic calibration, plus validation against observations where available.

## Hydrology Engine Notes

The hydrology foundation uses a strict downhill D8 raster graph. Direction codes follow the common ESRI-style convention: 1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 64=N, 128=NE. Flat cells and local sinks remain direction 0. Flow accumulation is upstream cell count including the cell itself. Drainage is a screening mask based on a configurable accumulation threshold in cells.

Watershed delineation traces all valid upstream cells to an outlet. When no outlet is supplied to `HydrologyEngine.run()`, automatic outlet selection chooses the valid cell with the greatest flow accumulation and immediately writes `watershed.tif`. This is a reproducible screening heuristic rather than a guaranteed hydrologic basin outlet.

Stream ordering uses Strahler ordering on thresholded stream cells. This remains a terrain-derived screening layer. Future work should add depression treatment, physically informed precipitation/runoff transformation, watershed-level diagnostics, and optional integration with pywatershed or other physically based components.

## Not Yet Verified

- Full Streamlit application startup on the target Windows machine.
- End-to-end multi-tile processing across a real multi-tile boundary.
- Live polygon extent processing against a downloaded DEM.
- Live contour/provenance generation on the target Windows run.
- Live HydrologyEngine execution against the produced DEM.
- Final passing CI result for the latest hydrology-to-climate integration commit.
- Live weather/climate retrieval against the configured default location.
- UI-level invocation of the new hydrology-to-climate pipeline from the Streamlit application.
- Hydrogeological evidence ingestion.
- MODFLOW 6 execution.
- Candidate ranking against real data.

## Immediate Next Actions

1. Verify CI for the hydrology-to-climate integration milestone.
2. Run HydrologyEngine on the real Windows DEM outputs and inspect flow accumulation/network/watershed behavior.
3. Exercise Open-Meteo historical and forecast retrieval against the project configuration.
4. Wire `qanat.pipeline.run_hydrology_climate` into the Streamlit execution flow so a saved project can run DEM -> watershed -> weather indicators from the UI.
5. Then move to hydrogeological evidence and groundwater/MODFLOW integration.

## Working Rule

After each meaningful milestone, update this file with what is actually implemented, what was tested, known failures, and exact next actions. Do not mark roadmap items complete based on design discussion alone.
