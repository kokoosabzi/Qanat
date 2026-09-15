# Qanat Project State

Updated: 2026-09-15

## Current Status

The repository contains the application/configuration foundation and an initial terrain engine. Terrain is still a research/engineering implementation and is not production-ready.

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

## Not Yet Verified

- Full Streamlit application startup on the target Windows machine.
- Live Copernicus download from the target environment.
- End-to-end multi-tile processing on real data.
- Polygon extent processing.
- Contour generation and terrain provenance metadata.
- Hydrology calculations.
- Weather/climate ingestion.
- Hydrogeological evidence ingestion.
- MODFLOW 6 execution.
- Candidate ranking against real data.
- CI status in GitHub Actions.

## Terrain Engine Notes

The engine uses the public Copernicus GLO-30 COG endpoint and Rasterio/PROJ locally. Copernicus GLO-30 is a DSM, not a bare-earth guarantee; this distinction must remain explicit in scientific reporting. Requested output resolution finer than the source DEM remains resampling, not creation of new terrain information.

The current multi-tile implementation mosaics intersecting one-degree source tiles before reprojection. The next terrain hardening step is polygon extent support plus explicit provenance/contour outputs.

## Previous Prototype Issue

An earlier standalone DEM prototype failed during circular clipping because `rasterio.transform.xy()` produced a flattened coordinate result while the DEM array remained 2D. `TerrainEngine.mask_to_radius()` now constructs shape-preserving pixel-center grids directly from the affine transform, with regression coverage.

## Immediate Next Actions

1. Run the terrain tests in the user's Windows environment.
2. Add polygon extent support and exact geometry masking.
3. Add contour generation and terrain metadata/provenance.
4. Verify real Copernicus acquisition and processing end-to-end.
5. Add hydrology engine after terrain artifacts are stable.
6. Only then connect external rainfall/climate datasets.

## Working Rule

After each meaningful milestone, update this file with what is actually implemented, what was tested, known failures, and exact next actions. Do not mark roadmap items complete based on design discussion alone.
