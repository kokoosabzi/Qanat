# Qanat Architecture Decisions

This is the durable decision log. Add a new dated entry for decisions that materially affect architecture, scientific methodology, data, or reproducibility.

## ADR-001 — Modular scientific engines

**Date:** 2026-09-15

**Decision:** Keep terrain, hydrology, climate, hydrogeology, groundwater, ranking and visualization as separate modules.

**Reason:** Scientific methods evolve independently and established engines such as MODFLOW 6/FloPy should remain replaceable behind clear interfaces.

## ADR-002 — Configuration is a first-class artifact

**Date:** 2026-09-15

**Decision:** A project configuration and run manifest are persistent artifacts, not UI-only state.

**Reason:** An AI agent must be able to resume work from the repository without relying on conversation history.

## ADR-003 — Evidence-based candidate ranking

**Date:** 2026-09-15

**Decision:** Candidate zones/corridors are ranked from explicit evidence layers and uncertainty. The initial ranking must be deterministic and explainable.

**Reason:** A black-box model cannot substitute for missing hydrogeological observations.

## ADR-004 — Source resolution is preserved

**Date:** 2026-09-15

**Decision:** Store native source resolution separately from requested output resolution.

**Reason:** Resampling a 30 m DEM to 10 m changes the grid but does not create new 10 m terrain information.

## ADR-005 — Groundwater modeling requires a conceptual model

**Date:** 2026-09-15

**Decision:** MODFLOW 6/FloPy integration is downstream of terrain, hydrology and hydrogeological evidence.

**Reason:** Numerical groundwater models require defensible conceptual structure and parameters. AI-generated guesses must not be silently treated as measurements.

## ADR-006 — Persistent agent handoff documents

**Date:** 2026-09-15

**Decision:** `AGENT_CONTEXT.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `PROJECT_STATE.md`, and `DECISIONS.md` form the minimum agent handoff layer.

**Reason:** Every new agent/session should be able to reconstruct project intent, architecture, current state and next actions by reading the repository.

## ADR-007 — External data provenance

**Date:** 2026-09-15

**Decision:** External datasets are referenced through source metadata, acquisition date, native resolution, CRS/units and checksums where practical; large datasets are not committed to Git.

**Reason:** Scientific reproducibility and repository size.
