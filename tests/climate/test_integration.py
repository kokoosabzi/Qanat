from dataclasses import dataclass

from qanat.climate import ClimateEngine, DailyWeather, watershed_indicators


@dataclass
class FakeProvider:
    def fetch_daily(self, latitude, longitude, start_date, end_date, *, mode="historical", timezone="auto"):
        assert latitude == 36.0
        assert longitude == 57.0
        assert start_date == "2026-01-01"
        assert end_date == "2026-01-02"
        assert mode == "historical"
        assert timezone == "auto"
        return DailyWeather(
            dates=("2026-01-01", "2026-01-02"),
            precipitation_mm=(100.0, 50.0),
            evapotranspiration_mm=(20.0, 20.0),
            source="fake",
            latitude=36.0,
            longitude=57.0,
        )


def test_provider_to_climate_to_watershed_indicators():
    climate, indicators = ClimateEngine.run_from_provider(
        FakeProvider(),
        36.0,
        57.0,
        "2026-01-01",
        "2026-01-02",
        watershed_area_m2=1000.0,
        runoff_coefficient=0.20,
        soil_storage_capacity_mm=100.0,
        initial_soil_storage_mm=50.0,
    )

    assert climate.precipitation_total_mm == 150.0
    assert climate.runoff_total_mm == 30.0
    assert indicators is not None
    assert indicators.watershed_area_m2 == 1000.0
    assert indicators.runoff_volume_m3 == 30.0
    assert indicators.recharge_indicator_volume_m3 == 30.0
    assert indicators.runoff_fraction_percent == 20.0
    assert indicators.recharge_indicator_fraction_percent == 20.0


def test_watershed_indicator_rejects_non_positive_area():
    climate = ClimateEngine.run(["2026-01-01"], [10.0], [1.0])
    for area in (0.0, -1.0):
        try:
            watershed_indicators(climate, area)
        except ValueError as exc:
            assert "watershed_area_m2" in str(exc)
        else:
            raise AssertionError("expected ValueError")
