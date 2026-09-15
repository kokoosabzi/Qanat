import numpy as np
from rasterio.transform import from_origin

from qanat.terrain import TerrainEngine


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
    assert np.count_nonzero(np.isfinite(result)) == 4
    assert np.isnan(result[0, 0])
    assert np.isfinite(result[2, 2])


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
