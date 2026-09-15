import numpy as np
import rasterio
from rasterio.transform import from_origin

from qanat.hydrology import HydrologyEngine


def test_d8_direction_on_monotonic_eastward_slope():
    dem = np.array(
        [
            [5, 4, 3],
            [5, 4, 3],
            [5, 4, 3],
        ],
        dtype=float,
    )

    direction = HydrologyEngine.flow_direction(dem)

    assert np.all(direction[:, 0] == 1)
    assert np.all(direction[:, 1] == 1)
    assert np.all(direction[:, 2] == 0)


def test_flow_accumulation_counts_upstream_cells():
    direction = np.array(
        [
            [1, 1, 0],
            [1, 1, 0],
            [1, 1, 0],
        ],
        dtype=np.uint8,
    )
    accumulation = HydrologyEngine.flow_accumulation(direction)

    assert accumulation[:, 0].tolist() == [1, 1, 1]
    assert accumulation[:, 1].tolist() == [2, 2, 2]
    assert accumulation[:, 2].tolist() == [0, 0, 0]


def test_drainage_mask_uses_threshold():
    accumulation = np.array([[1, 3, 5], [2, 4, 6]], dtype=float)

    mask = HydrologyEngine.drainage_mask(accumulation, threshold_cells=4)

    assert mask.tolist() == [[False, False, True], [False, True, True]]


def test_run_writes_hydrology_rasters(tmp_path):
    dem_path = tmp_path / "dem.tif"
    dem = np.array(
        [
            [6, 5, 4],
            [7, 6, 3],
            [8, 7, 2],
        ],
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

    result = HydrologyEngine(data_root=tmp_path).run(dem_path, threshold_cells=2)

    assert result.flow_direction_path.exists()
    assert result.flow_accumulation_path.exists()
    assert result.drainage_path.exists()

    with rasterio.open(result.flow_accumulation_path) as src:
        values = src.read(1)
        assert src.crs.to_epsg() == 32640
        assert values.max() >= 2
