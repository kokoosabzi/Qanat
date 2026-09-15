from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from typing import Literal, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class DailyWeather:
    """Provider-normalized daily weather values used by the climate engine."""

    dates: tuple[str, ...]
    precipitation_mm: tuple[float, ...]
    evapotranspiration_mm: tuple[float, ...]
    source: str
    latitude: float
    longitude: float


class ClimateProvider(Protocol):
    def fetch_daily(
        self,
        latitude: float,
        longitude: float,
        start_date: str | date,
        end_date: str | date,
        *,
        mode: Literal["historical", "forecast"] = "historical",
        timezone: str = "auto",
    ) -> DailyWeather:
        ...


class OpenMeteoProvider:
    """Open-Meteo adapter kept separate from the water-balance engine."""

    HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    SOURCE = "open-meteo"

    @staticmethod
    def _iso(value: str | date) -> str:
        return value.isoformat() if isinstance(value, date) else str(value)

    @staticmethod
    def _request_json(url: str, params: dict[str, str]) -> dict:
        query = urlencode(params)
        request = Request(
            f"{url}?{query}",
            headers={"User-Agent": "Qanat/0.1 climate-provider"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception as exc:  # pragma: no cover - network-specific failure
            raise RuntimeError(f"Open-Meteo request failed: {exc}") from exc

    def fetch_daily(
        self,
        latitude: float,
        longitude: float,
        start_date: str | date,
        end_date: str | date,
        *,
        mode: Literal["historical", "forecast"] = "historical",
        timezone: str = "auto",
    ) -> DailyWeather:
        start = self._iso(start_date)
        end = self._iso(end_date)
        if start > end:
            raise ValueError("start_date must be on or before end_date")
        if mode not in {"historical", "forecast"}:
            raise ValueError("mode must be 'historical' or 'forecast'")

        endpoint = self.HISTORICAL_URL if mode == "historical" else self.FORECAST_URL
        payload = self._request_json(
            endpoint,
            {
                "latitude": str(latitude),
                "longitude": str(longitude),
                "start_date": start,
                "end_date": end,
                "daily": "precipitation_sum,et0_fao_evapotranspiration",
                "timezone": timezone,
            },
        )
        daily = payload.get("daily")
        if not isinstance(daily, dict):
            raise RuntimeError("Open-Meteo response did not contain daily data")

        dates = tuple(str(value) for value in daily.get("time", []))
        precipitation = tuple(float(value or 0.0) for value in daily.get("precipitation_sum", []))
        evapotranspiration = tuple(
            float(value or 0.0) for value in daily.get("et0_fao_evapotranspiration", [])
        )
        if not dates or len(dates) != len(precipitation) or len(dates) != len(evapotranspiration):
            raise RuntimeError("Open-Meteo daily variables have inconsistent lengths")

        return DailyWeather(
            dates=dates,
            precipitation_mm=precipitation,
            evapotranspiration_mm=evapotranspiration,
            source=self.SOURCE,
            latitude=float(payload.get("latitude", latitude)),
            longitude=float(payload.get("longitude", longitude)),
        )
