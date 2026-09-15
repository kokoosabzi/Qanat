# Qanat Project State

Updated: 2026-09-15

## Current Status

The repository contains the application/configuration foundation and a validated Terrain Stage 2 implementation. Terrain is still a research/engineering implementation and is not production-ready.

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
- Terrain artifacts for elevation, slope, aspect, and hillshade.
- Regression coverage for the previous 2-D boolean-mask bug and tile selection across hemispheres/equator.
- GitHub Actions CI workflow for Python 3.11 and 3.12 test environments.

## Verified

### Automated tests

- Windows Python 3.12.10 virtual environment.
- `pytest -v`: 9 passed, 1 warning.
- The warning is a Rasterio internal `PendingDeprecationWarning` and is not currently treated as a project failure.

### Live Windows terrain run

- `TerrainEngine().run(ProjectConfig())` completed successfully on the target Windows environment.
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

- An earlier GitHub Actions failure was verified to belong to `main` commit `14aa21c68e7538e1ae0f3be533a92c316b15bae2`, not the current terrain branch.
- That old run expected 4 finite pixels for the radius-mask regression; the current branch correctly expects 5 based on pixel-center geometry.
- Current terrain branch HEAD is `913abb50013214608b2ea5e1617e3d67ae32ed17`.
- No GitHub Actions run is currently associated with that HEAD, so current-branch CI remains unverified.
- Do not merge Terrain Stage 2 until CI has run against the current branch HEAD and is green.

## Not Yet Verified

- Full Streamlit application startup on the target Windows machine.
- End-to-end multi-tile processing across a real multi-tile boundary.
- Polygon extent processing.
- Contour generation and terrain provenance metadata.
- Hydrology calculations.
- Weather/climate ingestion.
- Hydrogeological evidence ingestion.
- MODFLOW 6 execution.
- Candidate ranking against real data.
- GitHub Actions CI status for the current branch.

## Terrain Engine Notes

The engine uses the public Copernicus GLO-30 COG endpoint and Rasterio/PROJ locally. Copernicus GLO-30 is a DSM, not a bare-earth guarantee; this distinction must remain explicit in scientific reporting. Requested output resolution finer than the source DEM remains resampling, not creation of new terrain information.

The current multi-tile implementation mosaics intersecting one-degree source tiles before reprojection. The current verified live run used the default 5 km study area and produced valid terrain artifacts. The next terrain hardening step is polygon extent support plus explicit provenance/contour outputs.

## Previous Prototype Issue

An earlier standalone DEM prototype failed during circular clipping because `rasterio.transform.xy()` produced a flattened coordinate result while the DEM array remained 2D. `TerrainEngine.mask_to_radius()` now constructs shape-preserving pixel-center grids directly from the affine transform, with regression coverage.

## Immediate Next Actions

1. Trigger and verify GitHub Actions CI on the current terrain branch HEAD.
2. Keep PR #1 unmerged until current-branch CI is green.
3. Add polygon extent support and exact geometry masking.
4. Add contour generation and terrain metadata/provenance.
5. Add hydrology engine after terrain artifacts are stable.
6. Only then connect external rainfall/climate datasets.

## Working Rule

After each meaningful milestone, update this file with what is actually implemented, what was tested, known failures, and exact next actions. Do not mark roadmap items complete based on design discussion alone.
