# Qanat 0.1.0 Stable Freeze

Stable milestone: `Qanat 0.1.0`

Frozen commit:

```text
7d608f4d1e8f8ad6ff94681ad1e0bd03d67b4ddc
```

Stable branch:

```text
stable/0.1.0
```

## Verification basis

- Commit `5f72392150951291002277eaea3a74f6559c796c` is the immediately preceding implementation commit whose GitHub Actions CI completed successfully on Python 3.11 and 3.12 with **36 passed tests**.
- The frozen commit `7d608f4d...` differs from that green implementation commit only in `README.md`, `docs/PROJECT_STATE.md`, and `docs/SETUP.md`.
- No executable package or test file differs between those two commits.
- A fresh CI run for the frozen commit is still in progress at the time of this freeze record; therefore this document does not claim a second independent green run for the exact frozen SHA.

## Scope

Included:

- project configuration and validation
- Streamlit UI and execution button
- Copernicus GLO-30 terrain acquisition/processing
- elevation, slope, aspect, hillshade, contours and terrain provenance
- deterministic D8 flow direction/accumulation/drainage
- automatic outlet selection and watershed raster
- Strahler stream order and drainage network
- historical Open-Meteo precipitation and ET0 adapter
- deterministic climate water-balance indicators
- watershed-scale runoff/recharge-indicator/deficit volumes
- terrain → hydrology → climate orchestration
- automated regression suite

Excluded from 0.1.0:

- hydrogeological evidence ingestion
- calibrated groundwater recharge
- MODFLOW 6/FloPy execution
- AI evidence fusion/ranking
- forecast comparison workflow
- production 3D/video pipeline
- field validation

## Local test target

Use the `stable/0.1.0` branch for the first clean Windows checkout and run the commands in `docs/SETUP.md`.
