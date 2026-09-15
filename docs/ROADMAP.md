# Qanat Roadmap

This roadmap is a living plan. Implementation status belongs in `PROJECT_STATE.md`.

## Phase 0 — Foundation

- [x] repository initialized
- [x] project configuration concept
- [x] initial Streamlit application direction
- [x] persistent agent context
- [x] architecture document
- [ ] CI baseline
- [ ] complete configuration tests

## Phase 1 — Data Foundation

- [ ] dataset/source registry
- [ ] DEM acquisition abstraction
- [ ] raster metadata/provenance
- [ ] satellite/land-cover acquisition abstraction
- [ ] rainfall/climate acquisition abstraction
- [ ] well/spring/qanat observation schemas
- [ ] local cache layout

## Phase 2 — Terrain Engine

- [ ] CRS normalization
- [ ] DEM clipping/reprojection
- [ ] elevation statistics
- [ ] slope
- [ ] aspect
- [ ] hillshade
- [ ] curvature / terrain indices
- [ ] contours
- [ ] reproducible terrain artifacts
- [ ] regression test for the previous DEM masking bug

## Phase 3 — Hydrology Engine

- [ ] sink/depression handling policy
- [ ] flow direction
- [ ] flow accumulation
- [ ] stream/drainage extraction
- [ ] watershed delineation
- [ ] topographic wetness/recharge indicators
- [ ] validation fixtures

## Phase 4 — Weather / Climate / Recharge Evidence

- [ ] historical rainfall
- [ ] temperature
- [ ] evapotranspiration
- [ ] soil moisture
- [ ] drought/extreme-rain indicators
- [ ] seasonal and multi-year trends
- [ ] forecast ingestion with uncertainty
- [ ] recharge proxy model

Important: forecast data must be represented probabilistically/with uncertainty where appropriate; long-range forecasts must not be presented as deterministic facts.

## Phase 5 — Hydrogeology

- [ ] geology layer schema
- [ ] faults/fractures schema
- [ ] springs/wells/qanat observations
- [ ] aquifer conceptual model
- [ ] evidence quality scoring
- [ ] geological/hydrological cross-analysis

## Phase 6 — Groundwater Modeling

- [ ] conceptual model schema
- [ ] model grid builder
- [ ] MODFLOW 6 integration
- [ ] FloPy integration
- [ ] recharge boundary
- [ ] hydraulic properties
- [ ] wells/rivers/drains/ET as supported by evidence
- [ ] observations and calibration
- [ ] sensitivity/uncertainty

Do not build a groundwater model from invented parameters merely to produce a map.

## Phase 7 — Evidence Fusion / AI

- [ ] deterministic evidence normalization
- [ ] configurable weights
- [ ] candidate-zone generation
- [ ] candidate-corridor generation
- [ ] uncertainty propagation
- [ ] explanation/report generator
- [ ] optional ML/LLM assistance constrained by scientific artifacts

AI should explain and combine evidence; it must not fabricate missing measurements.

## Phase 8 — 3D / Visualization

- [ ] interactive 2D map
- [ ] terrain 3D
- [ ] subsurface conceptual visualization
- [ ] candidate corridor visualization
- [ ] export scene
- [ ] animation/video pipeline

## Phase 9 — Operational Platform

- [ ] run queue
- [ ] persistent artifact store
- [ ] run history
- [ ] reproducibility hashes
- [ ] API
- [ ] user/project management if needed

## Definition of Done for Scientific Features

A feature is not considered complete until it has:

1. documented inputs and units;
2. documented source/provenance;
3. deterministic tests or trusted reference comparison;
4. explicit handling of nodata and uncertainty;
5. a reproducible output artifact;
6. UI exposure only after the underlying engine is stable.
