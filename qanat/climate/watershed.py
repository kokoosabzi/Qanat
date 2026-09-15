from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import ClimateResult


@dataclass(frozen=True)
class WatershedIndicators:
    """Watershed-scale conversions of daily climate water-balance indicators."""

    watershed_area_m2: float
    runoff_depth_mm: float
    recharge_indicator_depth_mm: float
    water_deficit_depth_mm: float
    runoff_volume_m3: float
    recharge_indicator_volume_m3: float
    water_deficit_volume_m3: float
    runoff_fraction_percent: float
    recharge_indicator_fraction_percent: float


def watershed_indicators(
    climate_result: ClimateResult,
    watershed_area_m2: float,
) -> WatershedIndicators:
    """Convert climate depth indicators to watershed volumes.

    This assumes the provider-derived climate series is spatially representative
    of the supplied watershed. The recharge value remains a screening proxy,
    not a calibrated groundwater-recharge estimate.
    """

    if watershed_area_m2 <= 0:
        raise ValueError("watershed_area_m2 must be positive")

    area_factor = float(watershed_area_m2) / 1000.0
    runoff_depth = climate_result.runoff_total_mm
    recharge_depth = climate_result.recharge_indicator_total_mm
    deficit_depth = climate_result.water_deficit_total_mm
    precipitation = climate_result.precipitation_total_mm

    return WatershedIndicators(
        watershed_area_m2=float(watershed_area_m2),
        runoff_depth_mm=runoff_depth,
        recharge_indicator_depth_mm=recharge_depth,
        water_deficit_depth_mm=deficit_depth,
        runoff_volume_m3=runoff_depth * area_factor,
        recharge_indicator_volume_m3=recharge_depth * area_factor,
        water_deficit_volume_m3=deficit_depth * area_factor,
        runoff_fraction_percent=(runoff_depth / precipitation * 100.0) if precipitation else 0.0,
        recharge_indicator_fraction_percent=(recharge_depth / precipitation * 100.0) if precipitation else 0.0,
    )
