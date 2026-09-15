from dataclasses import dataclass

import numpy as np
import rasterio
from rasterio.transform import from_origin

from qanat.climate import ClimateEngine
from qanat.climate.watershed import watershed_area_from_raster


@dataclass
class FakeProvider:
    def fetch_daily(self, latitude, longitude, start_date, end_date, *, mode="historical", timezone="auto"):
        from qanat.climate.providers import DailyWeather

        return DailyWeather(
            dates=("2026-01-01", "2026-01-02"),
            precipitation_mm=(100.0, 50.0),
            evapotranspiration_mm=(20.0, 20.0),
            source="test",
            latitude=float(latitude),
            longitude=float(longitude),
        )


def test_watershed_area_is_derived_from_positive_cells(tmp_path):
    path = tmp_path / "watershed.tif"
    mask = np.array([[0, 1], [1, 1]], dtype=np.uint8)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype="uint8",
        crs="EPSG:32640",
        transform=from_origin(500000, 4000060, 30, 30),
        nodata=0,
    ) as dst:
        dst.write(mask, 1)

    area, cells = watershed_area_from_raster(path)
    assert cells == 3
    assert area == 2700.0


def test_provider_pipeline_uses_watershed_raster_area(tmp_path):
    path = tmp_path / "watershed.tif"
    mask = np.array([[1, 1], [0, 0]], dtype=np.uint8)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype="uint8",
        crs="EPSG:32640",
        transform=from_origin(500000, 4000060, 30, 30),
        nodata=0,
    ) as dst:
        dst.write(mask, 1)

    _, indicators = ClimateEngine.run_from_provider(
        FakeProvider(),
        36.0,
        57.0,
        "2026-01-01",
        "2026-01-02",
        watershed_raster_path=path,
    )

    assert indicators is not None
    assert indicators.watershed_area_m2 == 1800.0
    assert indicators.watershed_cell_count == 2
    assert indicators.runoff_volume_m3 == 54.0
    assert indicators.recharge_indicator_volume_m3 == 54.0
