from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class ClimateResult:
    """Deterministic daily climate water-balance indicators.

    The recharge values are screening indicators, not calibrated groundwater
    recharge estimates. They depend on the explicit assumptions supplied to
    :meth:`ClimateEngine.run`.
    """

    dates: tuple[str, ...]
    precipitation_mm: tuple[float, ...]
    evapotranspiration_mm: tuple[float, ...]
    runoff_mm: tuple[float, ...]
    infiltration_mm: tuple[float, ...]
    water_deficit_mm: tuple[float, ...]
    recharge_indicator_mm: tuple[float, ...]
    soil_storage_mm: tuple[float, ...]
    precipitation_total_mm: float
    evapotranspiration_total_mm: float
    runoff_total_mm: float
    infiltration_total_mm: float
    water_deficit_total_mm: float
    recharge_indicator_total_mm: float
    final_soil_storage_mm: float
    provenance_path: Path | None = None


class ClimateEngine:
    """Provider-neutral precipitation/ET water-balance engine."""

    @staticmethod
    def _validate_series(
        dates: Sequence[str],
        precipitation_mm: Sequence[float],
        evapotranspiration_mm: Sequence[float],
    ) -> None:
        if not dates:
            raise ValueError("dates and climate series must not be empty")
        if len(dates) != len(precipitation_mm) or len(dates) != len(evapotranspiration_mm):
            raise ValueError("dates, precipitation, and evapotranspiration must have equal lengths")
        for name, values in (
            ("precipitation_mm", precipitation_mm),
            ("evapotranspiration_mm", evapotranspiration_mm),
        ):
            for value in values:
                if not math.isfinite(float(value)) or float(value) < 0:
                    raise ValueError(f"{name} values must be finite and non-negative")

    @staticmethod
    def _validate_parameters(
        runoff_coefficient: float,
        interception_mm: float,
        soil_storage_capacity_mm: float,
        initial_soil_storage_mm: float,
    ) -> None:
        if not 0 <= runoff_coefficient <= 1:
            raise ValueError("runoff_coefficient must be between 0 and 1")
        if interception_mm < 0:
            raise ValueError("interception_mm must be non-negative")
        if soil_storage_capacity_mm <= 0:
            raise ValueError("soil_storage_capacity_mm must be positive")
        if not 0 <= initial_soil_storage_mm <= soil_storage_capacity_mm:
            raise ValueError("initial_soil_storage_mm must be within soil storage capacity")

    @staticmethod
    def run(
        dates: Sequence[str],
        precipitation_mm: Sequence[float],
        evapotranspiration_mm: Sequence[float] | None = None,
        *,
        runoff_coefficient: float = 0.20,
        interception_mm: float = 0.0,
        soil_storage_capacity_mm: float = 100.0,
        initial_soil_storage_mm: float = 50.0,
        provenance_path: str | Path | None = None,
    ) -> ClimateResult:
        """Run a transparent daily water-balance indicator model.

        Per day:
        1. fixed interception is removed from precipitation;
        2. runoff is ``runoff_coefficient * available_precipitation``;
        3. the remainder becomes infiltration into soil storage;
        4. ET removes water from available soil water;
        5. water above soil storage capacity is reported as a recharge indicator.

        This deliberately avoids pretending that precipitation alone is
        groundwater recharge. Calibrated recharge requires additional soil,
        land-cover, ET, geology, and hydrologic information.
        """

        if evapotranspiration_mm is None:
            evapotranspiration_mm = [0.0] * len(dates)

        ClimateEngine._validate_series(dates, precipitation_mm, evapotranspiration_mm)
        ClimateEngine._validate_parameters(
            runoff_coefficient,
            interception_mm,
            soil_storage_capacity_mm,
            initial_soil_storage_mm,
        )

        runoff: list[float] = []
        infiltration: list[float] = []
        deficit: list[float] = []
        recharge: list[float] = []
        storage: list[float] = []

        soil = float(initial_soil_storage_mm)
        for precipitation, et in zip(precipitation_mm, evapotranspiration_mm):
            available_precipitation = max(float(precipitation) - interception_mm, 0.0)
            day_runoff = available_precipitation * runoff_coefficient
            day_infiltration = available_precipitation - day_runoff

            water_before_et = soil + day_infiltration
            actual_et = min(float(et), water_before_et)
            day_deficit = max(float(et) - water_before_et, 0.0)
            remaining = water_before_et - actual_et
            day_recharge = max(remaining - soil_storage_capacity_mm, 0.0)
            soil = min(remaining, soil_storage_capacity_mm)

            runoff.append(day_runoff)
            infiltration.append(day_infiltration)
            deficit.append(day_deficit)
            recharge.append(day_recharge)
            storage.append(soil)

        result = ClimateResult(
            dates=tuple(str(value) for value in dates),
            precipitation_mm=tuple(float(value) for value in precipitation_mm),
            evapotranspiration_mm=tuple(float(value) for value in evapotranspiration_mm),
            runoff_mm=tuple(runoff),
            infiltration_mm=tuple(infiltration),
            water_deficit_mm=tuple(deficit),
            recharge_indicator_mm=tuple(recharge),
            soil_storage_mm=tuple(storage),
            precipitation_total_mm=float(sum(precipitation_mm)),
            evapotranspiration_total_mm=float(sum(evapotranspiration_mm)),
            runoff_total_mm=float(sum(runoff)),
            infiltration_total_mm=float(sum(infiltration)),
            water_deficit_total_mm=float(sum(deficit)),
            recharge_indicator_total_mm=float(sum(recharge)),
            final_soil_storage_mm=float(soil),
        )

        if provenance_path is not None:
            path = Path(provenance_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "schema_version": "1.0",
                "model": "deterministic_daily_water_balance_indicator",
                "assumptions": {
                    "runoff_coefficient": runoff_coefficient,
                    "interception_mm": interception_mm,
                    "soil_storage_capacity_mm": soil_storage_capacity_mm,
                    "initial_soil_storage_mm": initial_soil_storage_mm,
                },
                "totals": {
                    "precipitation_mm": result.precipitation_total_mm,
                    "evapotranspiration_mm": result.evapotranspiration_total_mm,
                    "runoff_mm": result.runoff_total_mm,
                    "infiltration_mm": result.infiltration_total_mm,
                    "water_deficit_mm": result.water_deficit_total_mm,
                    "recharge_indicator_mm": result.recharge_indicator_total_mm,
                    "final_soil_storage_mm": result.final_soil_storage_mm,
                },
                "scientific_boundary": (
                    "recharge_indicator_mm is a screening proxy, not a calibrated "
                    "groundwater recharge estimate"
                ),
            }
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            result = ClimateResult(**{**result.__dict__, "provenance_path": path})

        return result
