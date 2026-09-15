# Qanat Project State

Updated: 2026-09-15

## Current Status

The repository contains the initial application/configuration foundation and persistent project documentation. The scientific engines are not yet production-ready.

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

## Not Yet Verified

- Full Streamlit application startup.
- End-to-end DEM acquisition.
- Terrain calculations.
- Hydrology calculations.
- Weather/climate ingestion.
- Hydrogeological evidence ingestion.
- MODFLOW 6 execution.
- Candidate ranking against real data.
- CI status.

## Previous Prototype Issue

An earlier standalone DEM prototype failed during circular clipping because `rasterio.transform.xy()` produced a flattened coordinate result while the DEM array remained 2D. The corrected approach is to calculate pixel-center coordinates directly from the affine transform or use a shape-preserving coordinate construction.

This bug should receive a regression test when the terrain engine is implemented.

## Immediate Next Actions

1. Inspect current Python files and complete configuration tests.
2. Add CI for lint/test and basic application import.
3. Implement a clean DEM data-source abstraction.
4. Implement DEM reprojection/clipping with shape-safe masking.
5. Produce elevation/slope/aspect/hillshade artifacts for a small fixture.
6. Add hydrology engine after terrain artifacts are stable.
7. Only then connect external rainfall/climate datasets.

## Working Rule

After each meaningful milestone, update this file with:

- what is actually implemented;
- what was tested;
- known failures;
- exact next actions.

Do not mark roadmap items complete based on design discussion alone.
