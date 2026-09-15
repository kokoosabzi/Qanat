import json
from io import BytesIO

from qanat.climate import OpenMeteoProvider


class FakeResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_open_meteo_provider_normalizes_daily_values(monkeypatch):
    payload = {
        "latitude": 36.39,
        "longitude": 57.68,
        "daily": {
            "time": ["2026-01-01", "2026-01-02"],
            "precipitation_sum": [12.5, 0.0],
            "et0_fao_evapotranspiration": [2.1, 3.2],
        },
    }

    def fake_urlopen(request, timeout):
        assert "start_date=2026-01-01" in request.full_url
        assert "end_date=2026-01-02" in request.full_url
        assert "precipitation_sum%2Cet0_fao_evapotranspiration" in request.full_url
        return FakeResponse(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr("qanat.climate.providers.urlopen", fake_urlopen)
    result = OpenMeteoProvider().fetch_daily(36.39, 57.68, "2026-01-01", "2026-01-02")

    assert result.dates == ("2026-01-01", "2026-01-02")
    assert result.precipitation_mm == (12.5, 0.0)
    assert result.evapotranspiration_mm == (2.1, 3.2)
    assert result.source == "open-meteo"


def test_open_meteo_provider_rejects_reversed_dates():
    try:
        OpenMeteoProvider().fetch_daily(36.39, 57.68, "2026-01-02", "2026-01-01")
    except ValueError as exc:
        assert "on or before" in str(exc)
    else:
        raise AssertionError("expected ValueError")
