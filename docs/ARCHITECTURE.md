# Qanat Architecture

## 1. Architectural Goal

Build a scientific decision-support system that can progress from simple terrain screening to evidence-based hydrogeological and groundwater modeling without coupling the UI to scientific computation.

## 2. Layered Architecture

### A. Presentation

Responsible for user interaction only:

- project creation/editing
- map display
- layer selection
- run configuration
- result inspection
- evidence/uncertainty display
- export controls

Initial implementation: Streamlit.

### B. Application Orchestration

Coordinates runs but contains no domain-specific numerical algorithms.

Responsibilities:

- load and validate project configuration
- resolve data sources
- create a reproducible run manifest
- invoke analysis engines in dependency order
- collect outputs and diagnostics
- publish run status

### C. Domain / Scientific Engines

Each engine consumes typed inputs and produces typed artifacts.

```text
TerrainEngine
  DEM → elevation/slope/aspect/hillshade/curvature/contours

HydrologyEngine
  DEM + terrain → flow direction/accumulation/watersheds/drainage indicators

ClimateEngine
  rainfall + temperature + ET + soil moisture → climate/recharge indicators

HydrogeologyEngine
  geology + faults + terrain + hydrology + observations → hydrogeological evidence

GroundwaterEngine
  conceptual model + parameter data → MODFLOW 6 simulations and diagnostics

RankingEngine
  evidence layers + weights + uncertainty → candidate zones/corridors + explanations

VisualizationEngine
  artifacts → maps/3D-ready data/rendering inputs
```

## 3. Data Architecture

Every input should have metadata:

```yaml
source:
  provider: ...
  dataset: ...
  access_method: ...
spatial:
  crs: ...
  extent: ...
  native_resolution: ...
temporal:
  start: ...
  end: ...
quality:
  nodata: ...
  processing: ...
provenance:
  acquired_at: ...
  checksum: ...
```

Do not store large raster datasets in Git. Store manifests, checksums, small fixtures and reproducible acquisition metadata.

## 4. Run Model

A run is immutable after creation except for status metadata.

```text
ProjectConfig
   ↓
RunManifest
   ├── input dataset identities
   ├── source versions
   ├── processing parameters
   ├── software version
   └── configuration hash
   ↓
Artifacts
   ├── terrain
   ├── hydrology
   ├── climate
   ├── hydrogeology
   ├── groundwater
   ├── ranking
   └── reports
```

This allows an agent to reconstruct what was done instead of relying on conversational memory.

## 5. Candidate Ranking

Candidate ranking must be evidence fusion, not a black-box statement such as “dig here”.

A candidate should contain:

- geometry
- score
- confidence/uncertainty
- contributing evidence
- conflicting evidence
- data gaps
- recommended validation observations

A future score can be expressed conceptually as:

```text
candidate_score = Σ(weight_i × normalized_evidence_i)
                  - uncertainty_penalty
                  - data_gap_penalty
```

Weights must be configurable and documented. The first implementation should be deterministic and explainable before introducing learned models.

## 6. Groundwater Modeling Boundary

MODFLOW 6 should be introduced only when the conceptual model and required inputs are adequate. FloPy is the Python orchestration layer.

Expected separation:

```text
Qanat conceptual model
        ↓
Groundwater model builder
        ↓
FloPy objects
        ↓
MODFLOW 6 executable
        ↓
heads / budget / observations
        ↓
validation + uncertainty
```

Do not hide missing aquifer parameters behind AI-generated defaults. Unknown parameters must remain explicit assumptions or calibrated quantities.

## 7. Visualization Boundary

Scientific artifacts should be renderer-neutral where possible.

- 2D: GeoTIFF/GeoPackage/GeoJSON and map-ready arrays.
- 3D: regular grids/meshes plus scalar fields.
- Video: renderer-specific scene descriptions generated from scientific artifacts.

The visualization layer must never alter scientific source data silently.

## 8. Dependency Strategy

Keep the core install lightweight. Heavy geospatial and numerical dependencies should be optional until the corresponding engine is implemented.

Prefer established open-source engines rather than duplicating their algorithms.

## 9. Testing Strategy

- Unit tests: configuration, geometry, normalization, scoring.
- Data-contract tests: CRS, units, shape, nodata and metadata.
- Engine tests: small deterministic fixtures.
- Integration tests: complete small synthetic pipeline.
- Scientific validation: compare selected outputs against trusted reference cases.

## 10. Future Distributed Execution

The architecture should eventually support long-running jobs without redesigning the domain layer:

```text
UI/API → Run Queue → Worker → Artifact Store → Results API/UI
```

Do not introduce a distributed queue until local reproducible runs are stable.
