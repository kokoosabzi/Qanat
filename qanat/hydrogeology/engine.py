from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

SUPPORTED_LAYERS = (
    "geology",
    "faults_fractures",
    "wells",
    "springs",
    "existing_qanats",
)


@dataclass(frozen=True)
class HydrogeologySource:
    layer: str
    path: Path
    feature_count: int
    geometry_types: tuple[str, ...]
    crs: str | None = None


@dataclass(frozen=True)
class HydrogeologyResult:
    sources: tuple[HydrogeologySource, ...]

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def feature_count(self) -> int:
        return sum(source.feature_count for source in self.sources)


class HydrogeologyEngine:
    """Provider-neutral inventory for hydrogeology evidence layers.

    This stage intentionally does not infer groundwater occurrence or yield.
    It validates and inventories supplied GeoJSON evidence so later ranking and
    groundwater models can consume a reproducible, traceable source registry.
    """

    @staticmethod
    def inspect_geojson(path: str | Path, *, layer: str) -> HydrogeologySource:
        if layer not in SUPPORTED_LAYERS:
            raise ValueError(f"unsupported hydrogeology layer: {layer}")

        source_path = Path(path)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)

        try:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid GeoJSON: {source_path}") from exc

        if payload.get("type") != "FeatureCollection":
            raise ValueError("hydrogeology source must be a GeoJSON FeatureCollection")

        features = payload.get("features")
        if not isinstance(features, list):
            raise ValueError("GeoJSON FeatureCollection must contain a features list")

        geometry_types: set[str] = set()
        for feature in features:
            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                raise ValueError("GeoJSON features must be Feature objects")
            geometry = feature.get("geometry")
            if geometry is None:
                continue
            if not isinstance(geometry, dict):
                raise ValueError("GeoJSON feature geometry must be an object or null")
            geometry_type = geometry.get("type")
            if geometry_type:
                geometry_types.add(str(geometry_type))

        crs_name: str | None = None
        crs = payload.get("crs")
        if isinstance(crs, dict):
            properties = crs.get("properties")
            if isinstance(properties, dict):
                name = properties.get("name") or properties.get("code")
                if name is not None:
                    crs_name = str(name)

        return HydrogeologySource(
            layer=layer,
            path=source_path,
            feature_count=len(features),
            geometry_types=tuple(sorted(geometry_types)),
            crs=crs_name,
        )

    @classmethod
    def inventory_directory(
        cls,
        data_root: str | Path = "data/raw/hydrogeology",
        layers: Iterable[str] = SUPPORTED_LAYERS,
    ) -> HydrogeologyResult:
        root = Path(data_root)
        sources: list[HydrogeologySource] = []
        for layer in layers:
            if layer not in SUPPORTED_LAYERS:
                raise ValueError(f"unsupported hydrogeology layer: {layer}")
            path = root / f"{layer}.geojson"
            if path.exists():
                sources.append(cls.inspect_geojson(path, layer=layer))
        return HydrogeologyResult(tuple(sources))
