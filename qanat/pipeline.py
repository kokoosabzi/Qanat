from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from qanat.climate import ClimateEngine, OpenMeteoProvider, WatershedIndicators
from qanat.climate.engine import ClimateResult
from qanat.config import ProjectConfig
from qanat.hydrology import HydrologyEngine, HydrologyResult
from qanat.terrain import TerrainEngine, TerrainResult


@dataclass(frozen=True)
class HydrologyClimateResult:
    terrain: TerrainResult
    hydrology: HydrologyResult
    climate: ClimateResult
    watershed_indicators: WatershedIndicators


def run_hydrology_climate(
    config: ProjectConfig,
    *,
    data_root: str | Path = "data",
    climate_provider=None,
    end_date: str | date | None = None,
    overwrite_dem: bool = False,
    drainage_threshold_cells: int = 10,
) -> HydrologyClimateResult:
    """Run terrain -> D8 watershed -> provider climate indicators for one project."""

    if drainage_threshold_cells < 1:
        raise ValueError("drainage_threshold_cells must be at least 1")

    root = Path(data_root)
    terrain = TerrainEngine(data_root=root).run(config, overwrite=overwrite_dem)
    hydrology = HydrologyEngine(data_root=root).run(
        terrain.dem_path,
        threshold_cells=drainage_threshold_cells,
    )
    if hydrology.watershed_path is None:
        raise RuntimeError("HydrologyEngine did not produce watershed.tif")

    end = date.fromisoformat(str(end_date)) if end_date is not None else date.today() - timedelta(days=1)
    start = end - timedelta(days=365 * config.weather.historical_years)
    provider = climate_provider or OpenMeteoProvider()
    provenance = root / "processed" / "climate" / "climate_provenance.json"
    climate, indicators = ClimateEngine.run_from_provider(
        provider,
        config.location.latitude,
        config.location.longitude,
        start.isoformat(),
        end.isoformat(),
        mode="historical",
        watershed_raster_path=hydrology.watershed_path,
        provenance_path=provenance,
    )
    if indicators is None:
        raise RuntimeError("ClimateEngine did not produce watershed indicators")

    return HydrologyClimateResult(terrain, hydrology, climate, indicators)
