import json

import pytest

from qanat.climate import ClimateEngine


def test_water_balance_produces_runoff_infiltration_and_recharge_indicator():
    result = ClimateEngine.run(
        ["2026-01-01", "2026-01-02"],
        [100.0, 50.0],
        [20.0, 20.0],
        runoff_coefficient=0.20,
        soil_storage_capacity_mm=100.0,
        initial_soil_storage_mm=50.0,
    )

    assert result.precipitation_total_mm == 150.0
    assert result.runoff_total_mm == 30.0
    assert result.infiltration_total_mm == 120.0
    assert result.water_deficit_total_mm == 0.0
    assert result.recharge_indicator_total_mm == 20.0
    assert result.final_soil_storage_mm == 100.0


def test_missing_et_is_zero_and_is_explicit_in_result():
    result = ClimateEngine.run(["2026-01-01"], [25.0])
    assert result.evapotranspiration_mm == (0.0,)
    assert result.infiltration_mm == (20.0,)
    assert result.recharge_indicator_mm == (0.0,)


def test_water_deficit_is_reported_when_et_exceeds_available_water():
    result = ClimateEngine.run(
        ["2026-01-01"],
        [0.0],
        [80.0],
        initial_soil_storage_mm=10.0,
    )
    assert result.water_deficit_mm == (70.0,)
    assert result.final_soil_storage_mm == 0.0


def test_provenance_is_written_with_model_assumptions(tmp_path):
    provenance = tmp_path / "climate_provenance.json"
    result = ClimateEngine.run(
        ["2026-01-01"],
        [10.0],
        [2.0],
        provenance_path=provenance,
    )

    assert result.provenance_path == provenance
    payload = json.loads(provenance.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"
    assert payload["model"] == "deterministic_daily_water_balance_indicator"
    assert payload["assumptions"]["runoff_coefficient"] == 0.20
    assert "screening proxy" in payload["scientific_boundary"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"runoff_coefficient": -0.1},
        {"runoff_coefficient": 1.1},
        {"soil_storage_capacity_mm": 0.0},
        {"initial_soil_storage_mm": 101.0, "soil_storage_capacity_mm": 100.0},
    ],
)
def test_invalid_parameters_are_rejected(kwargs):
    with pytest.raises(ValueError):
        ClimateEngine.run(["2026-01-01"], [10.0], [1.0], **kwargs)


def test_mismatched_series_lengths_are_rejected():
    with pytest.raises(ValueError, match="equal lengths"):
        ClimateEngine.run(["2026-01-01"], [10.0, 5.0], [1.0])
