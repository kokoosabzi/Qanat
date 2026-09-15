from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .climate import ClimateEngine, ClimateProvider, ClimateResult, WatershedIndicators
from .hydrology import HydrologyEngine, HydrologyResult


@dataclass(frozen=True)
class HydroClimateResult:
    """End-to-end hydrology + climate outputs for one DEM and project location."""

    hydrology: HydrologyResult
    climate: ClimateResult
    watershed: WatershedIndicators


def run_hydrology_climate(
    dem_path: str | Path,
    provider: ClimateProvider,
    *,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    data_root: str | Path = "data",
    threshold_cells: int = 10,
    outlet_row: int | None = None,
    outlet_col: int | None = None,
    mode: str = "historical",
    timezone: str = "auto",
    runoff_coefficient: float = 0.20,
    interception_mm: float = 0.0,
    soil_storage_capacity_mm: float = 100.0,
    initial_soil_storage_mm: float = 50.0,
    provenance_path: str | Path | None = None,
) -> HydroClimateResult:
    """Run D8 hydrology, delineate a watershed, then aggregate provider climate over it.

    The hydrology stage automatically selects the maximum-accumulation outlet when no
    outlet row/column is supplied. The resulting watershed raster is passed directly to
    the climate stage, so watershed area does not need to be entered manually.
    """

    hydrology = HydrologyEngine(data_root=data_root).run(
        dem_path,
        threshold_cells=threshold_cells,
        outlet_row=outlet_row,
        outlet_col=outlet_col,
    )
    if hydrology.watershed_path is None:
        raise RuntimeError("hydrology did not produce a watershed raster")

    climate, indicators = ClimateEngine.run_from_provider(
        provider,
        latitude,
        longitude,
        start_date,
        end_date,
        mode=mode,
        timezone=timezone,
        runoff_coefficient=runoff_coefficient,
        interception_mm=interception_mm,
        soil_storage_capacity_mm=soil_storage_capacity_mm,
        initial_soil_storage_mm=initial_soil_storage_mm,
        watershed_raster_path=hydrology.watershed_path,
        provenance_path=provenance_path,
    )
    if indicators is None:
        raise RuntimeError("climate did not produce watershed indicators")

    return HydroClimateResult(hydrology=hydrology, climate=climate, watershed=indicators)
