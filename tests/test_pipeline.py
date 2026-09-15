import numpy as np
import rasterio
from rasterio.transform import from_origin

from qanat.climate.providers import DailyWeather
from qanat.pipeline import run_hydrology_climate


class FakeProvider:
    def fetch_daily(self, latitude, longitude, start_date, end_date, *, mode="historical", timezone="auto"):
        return DailyWeather(
            dates=("2025-01-01", "2025-01-02"),
            precipitation_mm=(100.0, 50.0),
            evapotranspiration_mm=(20.0, 20.0),
            source="test",
            latitude=latitude,
            longitude=longitude,
        )


def test_hydrology_to_climate_pipeline_uses_generated_watershed(tmp_path):
    dem_path = tmp_path / "dem.tif"
    dem = np.array(
        [[9, 8, 7], [8, 7, 5], [7, 5, 1]],
        dtype=np.float32,
    )
    with rasterio.open(
        dem_path,
        "w",
        driver="GTiff",
        height=3,
        width=3,
        count=1,
        dtype="float32",
        crs="EPSG:32640",
        transform=from_origin(500000, 4000100, 30, 30),
        nodata=-9999,
    ) as dst:
        dst.write(dem, 1)

    result = run_hydrology_climate(
        dem_path,
        FakeProvider(),
        latitude=36.3916139,
        longitude=57.6854968,
        start_date="2025-01-01",
        end_date="2025-01-02",
        data_root=tmp_path,
        threshold_cells=1,
    )

    assert result.hydrology.watershed_path is not None
    assert result.hydrology.watershed_path.exists()
    assert result.watershed.watershed_cell_count > 0
    assert result.watershed.watershed_area_m2 == result.watershed.watershed_cell_count * 900.0
    assert result.watershed.runoff_depth_mm == result.climate.runoff_total_mm
    assert result.watershed.recharge_indicator_depth_mm == result.climate.recharge_indicator_total_mm
    assert result.watershed.runoff_volume_m3 == result.watershed.runoff_depth_mm * result.watershed.watershed_area_m2 / 1000.0
    assert result.watershed.recharge_indicator_volume_m3 == result.watershed.recharge_indicator_depth_mm * result.watershed.watershed_area_m2 / 1000.0
