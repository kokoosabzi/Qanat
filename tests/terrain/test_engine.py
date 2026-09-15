import json

import numpy as np
from pyproj import Transformer
from rasterio.transform import from_origin
from rasterio.warp import transform_bounds
from shapely.geometry import box

from qanat.config import ProjectConfig
from qanat.terrain import TerrainEngine, TerrainResult


def test_mask_to_radius_preserves_2d_shape_and_masks_outside():
    array = np.arange(25, dtype=float).reshape(5, 5)
    transform = from_origin(0, 5, 1, 1)

    result = TerrainEngine.mask_to_radius(
        array,
        transform,
        center_x=2.5,
        center_y=2.5,
        radius_m=1.1,
    )

    assert result.shape == array.shape
    assert np.count_nonzero(np.isfinite(result)) == 5
    assert np.isnan(result[0, 0])
    assert np.isfinite(result[2, 2])


def test_mask_to_polygon_uses_pixel_centers():
    array = np.arange(25, dtype=float).reshape(5, 5)
    polygon = box(57.680, 36.386, 57.685, 36.391)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32640", always_xy=True)
    min_x, min_y = transformer.transform(57.680, 36.386)
    max_x, max_y = transformer.transform(57.685, 36.391)
    transform = from_origin(min_x, max_y, (max_x - min_x) / 5, (max_y - min_y) / 5)

    result = TerrainEngine._mask_to_polygon(
        array,
        transform,
        "EPSG:32640",
        polygon,
    )

    assert result.shape == array.shape
    assert np.count_nonzero(np.isfinite(result)) == 25
    assert np.isfinite(result[2, 2])


def test_derive_contours_writes_wgs84_geojson(tmp_path):
    dem_path = tmp_path / "dem.tif"
    data = np.arange(100, dtype=np.float32).reshape(10, 10)
    from rasterio import open as rio_open

    with rio_open(
        dem_path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype="float32",
        crs="EPSG:32640",
        transform=from_origin(500000, 4000100, 30, 30),
        nodata=-9999,
    ) as dst:
        dst.write(data, 1)

    engine = TerrainEngine(data_root=tmp_path)
    contour_path = engine.derive_contours(dem_path, interval_m=20)
    payload = json.loads(contour_path.read_text(encoding="utf-8"))

    assert payload["type"] == "FeatureCollection"
    assert payload["features"]
    assert {feature["properties"]["elev_m"] % 20 for feature in payload["features"]} == {0}
    assert payload["features"][0]["geometry"]["type"] == "LineString"


def test_write_provenance_records_inputs_and_outputs(tmp_path):
    engine = TerrainEngine(data_root=tmp_path)
    source = tmp_path / "raw" / "dem" / "copernicus_N36_E057_30m.tif"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"placeholder")
    result = TerrainResult(dem_path=tmp_path / "dem.tif")

    path = engine.write_provenance(ProjectConfig(), [source], result)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    assert payload["source_dem"]["provider"] == "Copernicus GLO-30"
    assert payload["source_dem"]["paths"] == [str(source)]
    assert payload["outputs"]["dem"] == str(result.dem_path)


def test_copernicus_tile_url_for_target():
    url = TerrainEngine.tile_url(36.3916139, 57.6854968)
    assert "N36_00_E057_00" in url
    assert url.endswith(".tif")


def test_copernicus_tile_url_supports_southern_and_western_hemispheres():
    url = TerrainEngine.tile_url(-12.3, -45.7)
    assert "S13_00_W046_00" in url
    assert url.endswith(".tif")


def test_tiles_for_bounds_crossing_equator_and_prime_meridian():
    tiles = TerrainEngine.tiles_for_bounds(-0.2, -0.2, 0.2, 0.2)
    assert set(tiles) == {(-1, -1), (-1, 0), (0, -1), (0, 0)}


def test_tiles_for_bounds_excludes_right_and_top_boundary_tile():
    tiles = TerrainEngine.tiles_for_bounds(57.1, 36.1, 58.0, 37.0)
    assert set(tiles) == {(36, 57)}
