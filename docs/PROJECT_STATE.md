# Qanat Project State

Updated: 2026-09-15

## Current Status

The repository now contains the initial application/configuration foundation plus the first terrain-engine implementation. The terrain engine is an initial research/engineering implementation, not yet production-ready.

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

- Repository: `kokoosabzi/Qanat`
- Main branch: `main`
- Python project metadata exists.
- Streamlit application direction exists.
- Configuration/domain package exists at a foundation level.
- Persistent architecture/context/roadmap documentation added.
- Initial `qanat.terrain` package added.
- Copernicus GLO-30 Public tile acquisition is implemented for northern/eastern tiles.
- Local DEM reprojection to a local UTM CRS and configurable output resolution is implemented.
- Terrain artifacts for elevation, slope, aspect, and hillshade are implemented.
- Regression test added for the previous 2-D boolean-mask shape bug.

## Not Yet Verified

- Full Streamlit application startup.
- Live Copernicus download from the target environment.
- End-to-end DEM acquisition and terrain processing on the target Windows machine.
- Contour generation.
- Hydrology calculations.
- Weather/climate ingestion.
- Hydrogeological evidence ingestion.
- MODFLOW 6 execution.
- Candidate ranking against real data.
- CI status.

## Terrain Engine Notes

The engine currently uses the public Copernicus GLO-30 COG endpoint and Rasterio/PROJ locally. Copernicus GLO-30 is a DSM, not a bare-earth guarantee; this distinction must remain explicit in scientific reporting. The current acquisition path intentionally supports the target's northern/eastern tile convention first and should be generalized to signed hemispheres and multiple tiles before being treated as a general global adapter.

Requested output resolution finer than the source DEM remains resampling, not creation of new terrain information.

## Previous Prototype Issue

An earlier standalone DEM prototype failed during circular clipping because `rasterio.transform.xy()` produced a flattened coordinate result while the DEM array remained 2D. The new `TerrainEngine.mask_to_radius()` constructs shape-preserving pixel-center grids directly from the affine transform, and a regression test covers the failure mode.

## Immediate Next Actions

1. Run the new terrain tests in the user's Windows environment.
2. Add CI for tests and basic application import.
3. Generalize DEM acquisition to signed hemispheres and multiple intersecting tiles.
4. Add polygon extent support and exact circular clipping in projected metres to the main processing path.
5. Add contour generation and terrain metadata/provenance.
6. Add hydrology engine after terrain artifacts are stable.
7. Only then connect external rainfall/climate datasets.

## Working Rule

After each meaningful milestone, update this file with:

- what is actually implemented;
- what was tested;
- known failures;
- exact next actions.

Do not mark roadmap items complete based on design discussion alone.
