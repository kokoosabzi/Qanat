import json

import numpy as np
import rasterio
from rasterio.transform import from_origin

from qanat.hydrology import HydrologyEngine


def test_d8_direction_on_monotonic_eastward_slope():
    dem = np.array([[5, 4, 3], [5, 4, 3], [5, 4, 3]], dtype=float)
    direction = HydrologyEngine.flow_direction(dem)
    assert np.all(direction[:, 0] == 1)
    assert np.all(direction[:, 1] == 1)
    assert np.all(direction[:, 2] == 0)


def test_flow_accumulation_counts_upstream_cells():
    direction = np.array([[1, 1, 0], [1, 1, 0], [1, 1, 0]], dtype=np.uint8)
    accumulation = HydrologyEngine.flow_accumulation(direction)
    assert accumulation[:, 0].tolist() == [1, 1, 1]
    assert accumulation[:, 1].tolist() == [2, 2, 2]
    assert accumulation[:, 2].tolist() == [0, 0, 0]


def test_select_outlet_returns_maximum_accumulation_cell():
    accumulation = np.array([[1, 3, 2], [4, 9, 5]], dtype=float)
    assert HydrologyEngine.select_outlet(accumulation) == (1, 1)


def test_stream_order_assigns_strahler_orders():
    direction = np.array([[4, 0, 4], [2, 0, 8], [0, 1, 0]], dtype=np.uint8)
    accumulation = np.array([[2, 0, 2], [2, 0, 2], [0, 4, 0]], dtype=float)
    order = HydrologyEngine.stream_order(direction, accumulation, threshold_cells=2)
    assert order[0, 0] == 1
    assert order[0, 2] == 1
    assert order[2, 1] == 2
    assert order.max() >= 2


def test_drainage_mask_uses_threshold():
    accumulation = np.array([[1, 3, 5], [2, 4, 6]], dtype=float)
    mask = HydrologyEngine.drainage_mask(accumulation, threshold_cells=4)
    assert mask.tolist() == [[False, False, True], [False, True, True]]


def test_delineate_watershed_follows_upstream_cells():
    direction = np.array([[1, 2, 2], [1, 1, 0], [1, 8, 0]], dtype=np.uint8)
    valid = np.ones_like(direction, dtype=bool)
    watershed = HydrologyEngine.delineate_watershed(
        direction, outlet_row=1, outlet_col=2, valid=valid
    )
    assert watershed[1, 2]
    assert watershed[0, 1]
    assert watershed[0, 0]
    assert watershed[1, 0]
    # Cell (2, 0) drains to (2, 1), then leaves the raster, so it is not upstream.
    assert not watershed[2, 0]
    assert not watershed[2, 2]


def test_drainage_network_geojson_contains_thresholded_links():
    direction = np.array([[1, 1, 0]], dtype=np.uint8)
    accumulation = np.array([[1, 2, 0]], dtype=float)
    transform = from_origin(500000, 4000030, 30, 30)
    valid = np.ones_like(direction, dtype=bool)
    payload = HydrologyEngine.drainage_network_geojson(
        direction,
        accumulation,
        transform,
        "EPSG:32640",
        threshold_cells=2,
        valid=valid,
    )
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) == 1
    assert payload["features"][0]["geometry"]["type"] == "LineString"
    assert payload["features"][0]["properties"]["accumulation_cells"] == 2.0


def test_run_writes_hydrology_outputs(tmp_path):
    dem_path = tmp_path / "dem.tif"
    dem = np.array([[6, 5, 4], [7, 6, 3], [8, 7, 2]], dtype=np.float32)
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
    result = HydrologyEngine(data_root=tmp_path).run(
        dem_path, threshold_cells=2, outlet_row=2, outlet_col=2
    )
    assert result.flow_direction_path.exists()
    assert result.flow_accumulation_path.exists()
    assert result.drainage_path.exists()
    assert result.drainage_network_path is not None and result.drainage_network_path.exists()
    assert result.stream_order_path is not None and result.stream_order_path.exists()
    assert result.watershed_path is not None and result.watershed_path.exists()
    with rasterio.open(result.flow_accumulation_path) as src:
        assert src.crs.to_epsg() == 32640
        assert src.read(1).max() >= 2
    payload = json.loads(result.drainage_network_path.read_text(encoding="utf-8"))
    assert payload["type"] == "FeatureCollection"
    with rasterio.open(result.stream_order_path) as src:
        assert src.read(1).max() >= 1
