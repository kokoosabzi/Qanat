from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import rasterio

if TYPE_CHECKING:
    from .engine import ClimateResult


@dataclass(frozen=True)
class WatershedIndicators:
    """Watershed-scale conversions of daily climate water-balance indicators."""

    watershed_area_m2: float
    watershed_cell_count: int
    runoff_depth_mm: float
    recharge_indicator_depth_mm: float
    water_deficit_depth_mm: float
    runoff_volume_m3: float
    recharge_indicator_volume_m3: float
    water_deficit_volume_m3: float
    runoff_fraction_percent: float
    recharge_indicator_fraction_percent: float


def watershed_area_from_raster(watershed_path: str | Path) -> tuple[float, int]:
    """Derive watershed area from positive cells and the raster pixel transform."""

    with rasterio.open(Path(watershed_path)) as src:
        mask = src.read(1)
        cell_area_m2 = abs(float(src.transform.a) * float(src.transform.e))
        if cell_area_m2 <= 0:
            raise ValueError("watershed raster has invalid pixel dimensions")
        cells = int(np.count_nonzero(np.isfinite(mask) & (mask > 0)))

    if cells <= 0:
        raise ValueError("watershed raster contains no positive cells")
    return cell_area_m2 * cells, cells


def watershed_indicators(
    climate_result: ClimateResult,
    watershed_area_m2: float,
    watershed_cell_count: int | None = None,
) -> WatershedIndicators:
    """Convert climate depth indicators to watershed volumes."""

    if watershed_area_m2 <= 0:
        raise ValueError("watershed_area_m2 must be positive")

    area_factor = float(watershed_area_m2) / 1000.0
    runoff_depth = climate_result.runoff_total_mm
    recharge_depth = climate_result.recharge_indicator_total_mm
    deficit_depth = climate_result.water_deficit_total_mm
    precipitation = climate_result.precipitation_total_mm

    return WatershedIndicators(
        watershed_area_m2=float(watershed_area_m2),
        watershed_cell_count=int(watershed_cell_count or 0),
        runoff_depth_mm=runoff_depth,
        recharge_indicator_depth_mm=recharge_depth,
        water_deficit_depth_mm=deficit_depth,
        runoff_volume_m3=runoff_depth * area_factor,
        recharge_indicator_volume_m3=recharge_depth * area_factor,
        water_deficit_volume_m3=deficit_depth * area_factor,
        runoff_fraction_percent=(runoff_depth / precipitation * 100.0) if precipitation else 0.0,
        recharge_indicator_fraction_percent=(recharge_depth / precipitation * 100.0) if precipitation else 0.0,
    )
