# Qanat Agent Context

> This file is the persistent handoff document for any AI agent continuing the Qanat project.
> Read this file before making architectural or implementation changes.

## Mission

Qanat is a configurable geospatial, hydrology, hydrogeology and groundwater-analysis platform for identifying and ranking candidate investigation zones and corridors for qanat/tunnel studies.

The system must combine terrain, hydrology, climate/weather, geology, groundwater evidence and uncertainty rather than treating terrain alone as proof of groundwater.

## Default Study Location

- Latitude: `36.3916139`
- Longitude: `57.6854968`
- Default extent: configurable; initial examples may use a 5 km radius.

All location and analysis settings must remain configurable. The default location is a project seed, not a hard-coded scientific assumption.

## Product Principles

1. Evidence before inference.
2. Preserve source resolution and provenance.
3. Never imply that a model guarantees groundwater, yield, tunnel safety, or excavation success.
4. Candidate routes/zones are investigation hypotheses requiring field validation.
5. Every important score should be explainable by contributing evidence and uncertainty.
6. Keep data acquisition, scientific engines, AI reasoning, and visualization modular.
7. Prefer established scientific engines over reimplementing mature numerical methods.
8. A finer output grid does not create finer source information.

## Scientific Engine Direction

Preferred components, introduced as needed:

- DEM/raster processing: Rasterio / GDAL ecosystem.
- Terrain/hydrology: QGIS, GRASS/SAGA, WhiteboxTools where appropriate.
- Hydrologic process simulation: pywatershed where justified.
- Groundwater flow/transport: MODFLOW 6.
- Python MODFLOW orchestration: FloPy.
- 3D visualization: PyVista/VTK and/or Blender for rendered media.
- Application UI: Streamlit for the early configurable MVP; keep the core independent from UI.

MODFLOW 6 and FloPy are modular; FloPy represents simulations as simulation/model/package/data layers. This project should preserve a similarly modular internal architecture rather than embedding groundwater logic inside the UI.

## System Pipeline

```text
Project Configuration
        ↓
Run Manifest / Provenance
        ↓
Data Acquisition & Catalog
  ├─ DEM
  ├─ Satellite / land cover
  ├─ Rainfall / climate
  ├─ Soil moisture / ET
  ├─ Geology / faults
  ├─ Wells / springs
  └─ Existing qanats
        ↓
Terrain Engine
        ↓
Hydrology Engine
        ↓
Recharge / Hydrogeology Evidence
        ↓
Groundwater Engine (MODFLOW 6 + FloPy when sufficient data exist)
        ↓
Evidence Fusion / Candidate Ranking
        ↓
Uncertainty + Evidence Report
        ↓
2D / 3D / Animation / Export
```

## Current Architecture

```text
app/                 UI and application entry points
qanat/               Scientific/domain code
  config/            configuration models and defaults
  core/              shared domain services
  terrain/           terrain analysis
  hydrology/         hydrologic analysis
  climate/           rainfall/weather/climate analysis
  hydrogeology/      geological and groundwater evidence
  groundwater/       MODFLOW/FloPy integration
  ranking/           evidence fusion and candidate ranking
  provenance/        source/run lineage
  visualization/     maps and 3D preparation
data/                local/generated data; never commit large datasets
projects/            project manifests and run metadata
configs/             versioned configuration presets
docs/                persistent architecture and agent context
tests/               tests
scripts/             repeatable developer/data utilities
```

## Configuration Contract

The canonical project configuration must support at least:

- location: latitude/longitude
- extent: radius, rectangle or polygon
- source DEM resolution and requested output resolution
- selectable data layers
- terrain/hydrology/groundwater/qanat/tunnel analyses
- weather historical period and forecast options
- output types: maps, 3D, report, animation/video

## AI Agent Rules

When continuing work:

1. Read `docs/AGENT_CONTEXT.md`.
2. Read `docs/ARCHITECTURE.md`.
3. Read `docs/ROADMAP.md`.
4. Read `docs/PROJECT_STATE.md` and compare it with the current Git tree.
5. Do not assume a feature is implemented merely because it is listed in the roadmap.
6. Update `PROJECT_STATE.md` after meaningful milestones.
7. Record major architecture decisions in `docs/DECISIONS.md`.
8. Keep scientific assumptions explicit and testable.
9. Before adding a new external dataset/API, record its source, license/terms, spatial/temporal resolution, units, and provenance strategy.
10. Before changing the public configuration schema, update the schema documentation and tests.

## Safety / Scientific Boundary

The platform is for geospatial and hydrogeological decision support. It must not present AI output as proof that water exists at a location or that a tunnel/excavation is safe. Any field implementation requires appropriate hydrogeological, geological and geotechnical verification and local professional review.
