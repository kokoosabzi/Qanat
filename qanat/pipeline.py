from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

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

    @property
    def watershed(self) -> WatershedIndicators:
        """Backward-compatible alias for older pipeline consumers."""
        return self.watershed_indicators


def run_hydrology_climate(
    config_or_dem: ProjectConfig | str | Path,
    provider: Any | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
    *,
    data_root: str | Path = "data",
    overwrite_dem: bool = False,
    drainage_threshold_cells: int = 10,
    threshold_cells: int | None = None,
) -> HydrologyClimateResult:
    """Run terrain -> D8 watershed -> provider climate indicators.

    Supports both the current ProjectConfig-driven API and the earlier DEM-driven
    API used by existing callers/tests.
    """

    if threshold_cells is not None:
        drainage_threshold_cells = threshold_cells
    if drainage_threshold_cells < 1:
        raise ValueError("drainage_threshold_cells must be at least 1")

    root = Path(data_root)
    if isinstance(config_or_dem, ProjectConfig):
        config = config_or_dem
        terrain = TerrainEngine(data_root=root).run(config, overwrite=overwrite_dem)
        dem_path = terrain.dem_path
        latitude = config.location.latitude
        longitude = config.location.longitude
        end_value = end_date if end_date is not None else date.today() - timedelta(days=1)
        end = date.fromisoformat(str(end_value))
        start = end - timedelta(days=365 * config.weather.historical_years)
        start_value = start
        climate_provider = provider or OpenMeteoProvider()
    else:
        dem_path = Path(config_or_dem)
        terrain = TerrainResult(dem_path=dem_path)
        if provider is None or latitude is None or longitude is None or start_date is None or end_date is None:
            raise ValueError("DEM-driven pipeline requires provider, latitude, longitude, start_date, and end_date")
        start_value = start_date
        end_value = end_date
        climate_provider = provider

    hydrology = HydrologyEngine(data_root=root).run(
        dem_path,
        threshold_cells=drainage_threshold_cells,
    )
    if hydrology.watershed_path is None:
        raise RuntimeError("HydrologyEngine did not produce watershed.tif")

    provenance = root / "processed" / "climate" / "climate_provenance.json"
    climate, indicators = ClimateEngine.run_from_provider(
        climate_provider,
        latitude,
        longitude,
        str(start_value),
        str(end_value),
        mode="historical",
        watershed_raster_path=hydrology.watershed_path,
        provenance_path=provenance,
    )
    if indicators is None:
        raise RuntimeError("ClimateEngine did not produce watershed indicators")

    return HydrologyClimateResult(terrain, hydrology, climate, indicators)
