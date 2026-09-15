# Qanat Project State

Updated: 2026-09-15

## Current Status

The repository contains the application/configuration foundation, a validated Terrain Stage 2 implementation, terrain contour/provenance outputs, and a deterministic Hydrology engine with D8, flow accumulation, watershed delineation, and drainage-network vectorization. Terrain and hydrology are still research/engineering implementations and are not production-ready.

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
- `qanat.hydrology` D8 flow direction and flow accumulation.
- Thresholded drainage screening mask.
- Upstream watershed delineation from a selected outlet cell.
- Thresholded D8 drainage-network vectorization to WGS84 GeoJSON.
- Regression coverage for radius masking, polygon masking, hemispheres, equator/prime-meridian tile boundaries, contours, provenance, D8, accumulation, watershed delineation, drainage vectorization, and raster outputs.
- GitHub Actions CI workflow for Python 3.11 and 3.12 test environments.

## Verified

### Automated tests

- Windows Python 3.12.10 virtual environment previously passed the terrain/config suite: 9 passed, 1 warning.
- The current watershed/drainage tests are committed but the newest branch head still requires CI verification.
- The Rasterio internal `PendingDeprecationWarning` is not currently treated as a project failure.

### Live Windows terrain run

- `TerrainEngine().run(ProjectConfig())` completed successfully on the target Windows environment before the polygon milestone.
- Output artifacts were created under `data/processed/terrain/`:
  - `dem.tif`
  - `slope.tif`
  - `aspect.tif`
  - `hillshade.tif`
- All four artifacts use `EPSG:32640` and 30 m × 30 m resolution.
- DEM dimensions: 338 × 337 pixels.
- DEM valid pixels after nodata masking: 87,258.
- DEM valid elevation range: 1397.6382 m to 2019.3392 m.
- Slope, aspect, and hillshade contain the same 87,258 valid pixels.
- The configured 5 km radius workflow completed without exception.

## CI Status

- Earlier GitHub Actions failure belonged to `main` commit `14aa21c68e7538e1ae0f3be533a92c316b15bae2`, not the terrain branch.
- The corrected radius-mask expectation is 5 finite pixel centers for the regression fixture.
- The latest known green run was `35014483526` with Python 3.11 and 3.12 jobs successful.
- Commit `5bcad34e520bf47251d176c4b54b19cabc524e5d` had no directly associated workflow run at the time it was checked.
- Commits `34e155a9eb47999595d8ccc167146920f937e80a` and `64b47ae8b3df66fb0df24c5e79b53a7f1822f273` extend hydrology functionality; current HEAD still requires fresh CI verification.

## Hydrology Engine Notes

The current hydrology foundation uses a strict downhill D8 raster graph. Direction codes follow the common ESRI-style convention: 1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 64=N, 128=NE. Flat cells and local sinks remain direction 0. Flow accumulation is upstream cell count including the cell itself. Drainage is a screening mask based on a configurable accumulation threshold in cells.

Watershed delineation follows the reverse D8 graph from a specified outlet cell. Drainage vectorization emits thresholded D8 cell-to-receiver links as WGS84 GeoJSON with accumulation and D8-code properties.

This is intentionally a transparent terrain-derived screening layer, not a complete hydrologic model. Future work should add depression treatment, stream ordering, basin/outlet selection helpers, precipitation/runoff inputs, and optional integration with pywatershed or other physically based components.

## Not Yet Verified

- Full Streamlit application startup on the target Windows machine.
- End-to-end multi-tile processing across a real multi-tile boundary.
- Live polygon extent processing against a downloaded DEM.
- Live contour/provenance generation on the target Windows run.
- Live HydrologyEngine execution against the produced DEM.
- CI for the current hydrology branch head.
- Weather/climate ingestion.
- Hydrogeological evidence ingestion.
- MODFLOW 6 execution.
- Candidate ranking against real data.

## Terrain Engine Notes

The engine uses the public Copernicus GLO-30 COG endpoint and Rasterio/PROJ locally. Copernicus GLO-30 is a DSM, not a bare-earth guarantee; this distinction must remain explicit in scientific reporting. Requested output resolution finer than the source DEM remains resampling, not creation of new terrain information.

Polygon extents are interpreted as GeoJSON Polygon or MultiPolygon geometries in EPSG:4326. Their bounding box determines source-tile acquisition and DEM windowing; exact masking is then performed after reprojection in the local UTM CRS using pixel-center semantics (`all_touched=False`).

The current multi-tile implementation mosaics intersecting one-degree source tiles before reprojection. The verified live run used the default 5 km radius study area and produced valid terrain artifacts.

## Previous Prototype Issue

An earlier standalone DEM prototype failed during circular clipping because `rasterio.transform.xy()` produced a flattened coordinate result while the DEM array remained 2D. `TerrainEngine.mask_to_radius()` now constructs shape-preserving pixel-center grids directly from the affine transform, with regression coverage.

## Immediate Next Actions

1. Verify CI for the current hydrology branch head.
2. Run the new HydrologyEngine on the real Windows DEM outputs.
3. Run the new polygon + contour + provenance workflow on Windows.
4. Add watershed outlet selection helpers and stream-ordering logic.
5. Only then connect external rainfall/climate datasets.

## Working Rule

After each meaningful milestone, update this file with what is actually implemented, what was tested, known failures, and exact next actions. Do not mark roadmap items complete based on design discussion alone.
