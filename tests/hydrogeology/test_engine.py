from __future__ import annotations

import json

import pytest

from qanat.hydrogeology import HydrogeologyEngine


def _write_geojson(path, features):
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )


def test_inspect_geojson_inventories_features_and_geometry_types(tmp_path):
    path = tmp_path / "wells.geojson"
    _write_geojson(
        path,
        [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [1, 2]}, "properties": {}},
            {"type": "Feature", "geometry": None, "properties": {}},
        ],
    )

    source = HydrogeologyEngine.inspect_geojson(path, layer="wells")

    assert source.layer == "wells"
    assert source.feature_count == 2
    assert source.geometry_types == ("Point",)


def test_inventory_directory_skips_missing_layers(tmp_path):
    path = tmp_path / "springs.geojson"
    _write_geojson(
        path,
        [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [1, 2]}, "properties": {}}],
    )

    result = HydrogeologyEngine.inventory_directory(tmp_path)

    assert result.source_count == 1
    assert result.feature_count == 1
    assert result.sources[0].layer == "springs"


def test_invalid_geojson_is_rejected(tmp_path):
    path = tmp_path / "geology.geojson"
    path.write_text('{"type":"Point","coordinates":[1,2]}', encoding="utf-8")

    with pytest.raises(ValueError, match="FeatureCollection"):
        HydrogeologyEngine.inspect_geojson(path, layer="geology")
