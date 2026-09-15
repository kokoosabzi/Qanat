from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from pyproj import CRS, Transformer
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject
from shapely.geometry import LineString, shape, mapping
from shapely.ops import transform as transform_geometry

from qanat.config import ProjectConfig


@dataclass(frozen=True)
class TerrainResult:
    """Paths and metadata produced by the terrain engine."""

    dem_path: Path
    slope_path: Path | None = None
    aspect_path: Path | None = None
    hillshade_path: Path | None = None
    contour_path: Path | None = None
    provenance_path: Path | None = None


class TerrainEngine:
    """Acquire Copernicus GLO-30 tiles and produce local terrain artifacts."""

    SOURCE_TEMPLATE = (
        "https://copernicus-dem-30m.s3.amazonaws.com/"
        "Copernicus_DSM_COG_10_{lat_hemi}{lat:02d}_00_{lon_hemi}{lon:03d}_00_DEM/"
        "Copernicus_DSM_COG_10_{lat_hemi}{lat:02d}_00_{lon_hemi}{lon:03d}_00_DEM.tif"
    )
    DEFAULT_CONTOUR_INTERVAL_M = 10.0

    def __init__(self, data_root: str | Path = "data") -> None:
        self.data_root = Path(data_root)
        self.raw_dir = self.data_root / "raw" / "dem"
        self.processed_dir = self.data_root / "processed" / "terrain"

    @staticmethod
    def _tile_indices(latitude: float, longitude: float) -> tuple[int, int]:
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("latitude/longitude outside valid geographic range")
        lat = int(np.floor(latitude))
        lon = int(np.floor(longitude))
        if latitude == 90:
            lat = 89
        if longitude == 180:
            lon = 179
        return lat, lon

    @classmethod
    def tile_url(cls, latitude: float, longitude: float) -> str:
        lat, lon = cls._tile_indices(latitude, longitude)
        lat_hemi = "N" if lat >= 0 else "S"
        lon_hemi = "E" if lon >= 0 else "W"
        return cls.SOURCE_TEMPLATE.format(
            lat_hemi=lat_hemi,
            lat=abs(lat),
            lon_hemi=lon_hemi,
            lon=abs(lon),
        )

    @classmethod
    def tiles_for_bounds(cls, left: float, bottom: float, right: float, top: float) -> list[tuple[int, int]]:
        """Return all one-degree tile indices intersecting geographic bounds."""
        if left > right or bottom > top:
            raise ValueError("invalid geographic bounds")
        min_lon = int(np.floor(left))
        max_lon = int(np.floor(np.nextafter(right, -np.inf)))
        min_lat = int(np.floor(bottom))
        max_lat = int(np.floor(np.nextafter(top, -np.inf)))
        return [
            (lat, lon)
            for lat in range(min_lat, max_lat + 1)
            for lon in range(min_lon, max_lon + 1)
            if -90 <= lat < 90 and -180 <= lon < 180
        ]

    def _tile_url_from_indices(self, lat: int, lon: int) -> str:
        return self.tile_url(lat + 0.5 if lat >= 0 else lat - 0.5, lon + 0.5 if lon >= 0 else lon - 0.5)

    def download_tile(self, latitude: float, longitude: float, overwrite: bool = False) -> Path:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        lat, lon = self._tile_indices(latitude, longitude)
        lat_hemi = "N" if lat >= 0 else "S"
        lon_hemi = "E" if lon >= 0 else "W"
        destination = self.raw_dir / f"copernicus_{lat_hemi}{abs(lat):02d}_{lon_hemi}{abs(lon):03d}_30m.tif"
        if destination.exists() and not overwrite:
            return destination
        url = self.tile_url(latitude, longitude)
        try:
            with urlopen(url, timeout=120) as response, destination.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return destination

    def download_sources(self, config: ProjectConfig, overwrite: bool = False) -> list[Path]:
        left, bottom, right, top = self._analysis_window(config)
        tiles = self.tiles_for_bounds(left, bottom, right, top)
        return [self.download_tile(lat + 0.5, lon + 0.5, overwrite=overwrite) for lat, lon in tiles]

    def download_source(self, config: ProjectConfig, overwrite: bool = False) -> Path:
        return self.download_tile(config.location.latitude, config.location.longitude, overwrite=overwrite)

    @staticmethod
    def _utm_crs(latitude: float, longitude: float) -> CRS:
        zone = int((longitude + 180) // 6) + 1
        zone = min(max(zone, 1), 60)
        epsg = 32600 + zone if latitude >= 0 else 32700 + zone
        return CRS.from_epsg(epsg)

    @staticmethod
    def _polygon_geometry(config: ProjectConfig):
        value = config.extent.polygon_geojson
        if not value:
            raise ValueError("polygon extent requires polygon_geojson")
        geometry = value.get("geometry") if value.get("type") == "Feature" else value
        if not isinstance(geometry, dict):
            raise ValueError("polygon_geojson must be a GeoJSON geometry or Feature")
        polygon = shape(geometry)
        if polygon.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError("polygon extent requires Polygon or MultiPolygon geometry")
        if polygon.is_empty or not polygon.is_valid:
            raise ValueError("polygon extent geometry must be non-empty and valid")
        return polygon

    @classmethod
    def _analysis_window(cls, config: ProjectConfig) -> tuple[float, float, float, float]:
        lat = config.location.latitude
        lon = config.location.longitude
        if config.extent.mode.value == "polygon":
            return cls._polygon_geometry(config).bounds
        if config.extent.mode.value == "radius":
            half_w = config.extent.radius_m / (111_320 * max(np.cos(np.deg2rad(lat)), 0.1))
            half_h = config.extent.radius_m / 110_540
        else:
            half_w = config.extent.width_m / (2 * 111_320 * max(np.cos(np.deg2rad(lat)), 0.1))
            half_h = config.extent.height_m / (2 * 110_540)
        return lon - half_w, lat - half_h, lon + half_w, lat + half_h

    @staticmethod
    def _open_mosaic(source_paths: list[str | Path]):
        datasets = [rasterio.open(path) for path in source_paths]
        try:
            mosaic, transform = merge(datasets, indexes=1)
            profile = datasets[0].profile.copy()
        finally:
            for dataset in datasets:
                dataset.close()
        return mosaic[0], transform, profile

    @classmethod
    def _mask_to_polygon(cls, array: np.ndarray, transform, dst_crs: CRS, polygon) -> np.ndarray:
        transformer = Transformer.from_crs("EPSG:4326", dst_crs, always_xy=True)
        projected = transform_geometry(transformer.transform, polygon)
        inside = geometry_mask(
            [projected.__geo_interface__],
            out_shape=array.shape,
            transform=transform,
            invert=True,
            all_touched=False,
        )
        result = array.astype(float, copy=True)
        result[~inside] = np.nan
        return result

    def process_dem(self, source_path: str | Path | list[str | Path], config: ProjectConfig) -> Path:
        """Reproject, resample and precisely clip a source DEM."""
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.processed_dir / "dem.tif"
        dst_crs = self._utm_crs(config.location.latitude, config.location.longitude)
        left, bottom, right, top = self._analysis_window(config)
        sources = source_path if isinstance(source_path, list) else [source_path]
        source_array, source_transform, profile = self._open_mosaic(sources)
        src_crs = profile["crs"]
        window = rasterio.windows.from_bounds(left, bottom, right, top, source_transform)
        window = window.round_offsets().round_lengths()
        window = window.intersection(rasterio.windows.Window(0, 0, source_array.shape[1], source_array.shape[0]))
        if window.width <= 0 or window.height <= 0:
            raise ValueError("Configured analysis extent does not overlap the source DEM")
        row0, col0 = int(window.row_off), int(window.col_off)
        row1, col1 = row0 + int(window.height), col0 + int(window.width)
        data = source_array[row0:row1, col0:col1]
        src_transform = rasterio.windows.transform(window, source_transform)
        src_nodata = profile.get("nodata") if profile.get("nodata") is not None else -9999.0
        transform, width, height = calculate_default_transform(
            src_crs,
            dst_crs,
            data.shape[1],
            data.shape[0],
            *rasterio.windows.bounds(window, source_transform),
            resolution=config.resolution.output_m,
        )
        destination = np.full((height, width), src_nodata, dtype=np.float32)
        reproject(
            source=data.astype(np.float32),
            destination=destination,
            src_transform=src_transform,
            src_crs=src_crs,
            src_nodata=src_nodata,
            dst_transform=transform,
            dst_crs=dst_crs,
            dst_nodata=src_nodata,
            resampling=Resampling.bilinear,
        )

        if config.extent.mode.value == "radius":
            transformer = Transformer.from_crs("EPSG:4326", dst_crs, always_xy=True)
            center_x, center_y = transformer.transform(config.location.longitude, config.location.latitude)
            clipped = self.mask_to_radius(destination.astype(float), transform, center_x, center_y, config.extent.radius_m)
            destination = np.where(np.isfinite(clipped), clipped, src_nodata).astype(np.float32)
        elif config.extent.mode.value == "polygon":
            clipped = self._mask_to_polygon(destination, transform, dst_crs, self._polygon_geometry(config))
            destination = np.where(np.isfinite(clipped), clipped, src_nodata).astype(np.float32)

        profile.update(
            driver="GTiff",
            height=height,
            width=width,
            count=1,
            dtype="float32",
            crs=dst_crs,
            transform=transform,
            nodata=src_nodata,
            compress="deflate",
            tiled=True,
        )
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(destination, 1)
            dst.set_band_description(1, "elevation_m")
        return output_path

    @staticmethod
    def _metric_grid(transform, shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
        rows, cols = np.indices(shape)
        xs = transform.c + (cols + 0.5) * transform.a + (rows + 0.5) * transform.b
        ys = transform.f + (cols + 0.5) * transform.d + (rows + 0.5) * transform.e
        return xs, ys

    @classmethod
    def mask_to_radius(cls, array: np.ndarray, transform, center_x: float, center_y: float, radius_m: float) -> np.ndarray:
        xs, ys = cls._metric_grid(transform, array.shape)
        inside = (xs - center_x) ** 2 + (ys - center_y) ** 2 <= radius_m**2
        result = array.copy()
        result[~inside] = np.nan
        return result

    def derive_contours(self, dem_path: str | Path, interval_m: float = DEFAULT_CONTOUR_INTERVAL_M) -> Path:
        """Generate WGS84 GeoJSON contour lines from a projected DEM."""
        if interval_m <= 0:
            raise ValueError("contour interval must be greater than zero")
        dem_path = Path(dem_path)
        output_path = self.processed_dir / "contours.geojson"
        with rasterio.open(dem_path) as src:
            dem = src.read(1).astype(float)
            nodata = src.nodata
            valid = np.isfinite(dem) if nodata is None else np.isfinite(dem) & (dem != nodata)
            if not valid.any():
                raise ValueError("DEM contains no valid pixels")
            masked = np.ma.masked_where(~valid, dem)
            rows, cols = np.indices(dem.shape)
            xs = src.transform.c + (cols + 0.5) * src.transform.a + (rows + 0.5) * src.transform.b
            ys = src.transform.f + (cols + 0.5) * src.transform.d + (rows + 0.5) * src.transform.e
            min_elev = float(dem[valid].min())
            max_elev = float(dem[valid].max())
            first = np.ceil(min_elev / interval_m) * interval_m
            levels = np.arange(first, max_elev + interval_m * 0.5, interval_m)
            figure = plt.figure()
            try:
                contour_set = plt.contour(xs, ys, masked, levels=levels)
                transformer = Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
                features = []
                for level, collection in zip(contour_set.levels, contour_set.allsegs):
                    for segment in collection:
                        if len(segment) < 2:
                            continue
                        projected_line = LineString(segment)
                        geographic_line = transform_geometry(transformer.transform, projected_line)
                        features.append(
                            {
                                "type": "Feature",
                                "properties": {"elev_m": float(level)},
                                "geometry": mapping(geographic_line),
                            }
                        )
            finally:
                plt.close(figure)
        payload = {
            "type": "FeatureCollection",
            "name": "qanat_contours",
            "features": features,
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return output_path

    def write_provenance(
        self,
        config: ProjectConfig,
        source_paths: list[Path],
        result: TerrainResult,
    ) -> Path:
        """Write machine-readable lineage metadata for the terrain run."""
        output_path = self.processed_dir / "terrain_provenance.json"
        payload = {
            "schema_version": 1,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "engine": "qanat.terrain.TerrainEngine",
            "project_name": config.name,
            "location": config.location.model_dump(),
            "extent": config.extent.model_dump(mode="json"),
            "resolution": config.resolution.model_dump(),
            "source_dem": {
                "provider": "Copernicus GLO-30",
                "paths": [str(path) for path in source_paths],
                "source_resolution_m": config.resolution.source_dem_m,
            },
            "outputs": {
                "dem": str(result.dem_path),
                "slope": str(result.slope_path) if result.slope_path else None,
                "aspect": str(result.aspect_path) if result.aspect_path else None,
                "hillshade": str(result.hillshade_path) if result.hillshade_path else None,
                "contours": str(result.contour_path) if result.contour_path else None,
            },
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def derive_terrain(self, dem_path: str | Path, config: ProjectConfig) -> TerrainResult:
        dem_path = Path(dem_path)
        outputs: dict[str, Path | None] = {"slope_path": None, "aspect_path": None, "hillshade_path": None}
        with rasterio.open(dem_path) as src:
            dem = src.read(1).astype(np.float32)
            nodata = src.nodata
            valid = np.isfinite(dem) if nodata is None else dem != nodata
            if not valid.any():
                raise ValueError("DEM contains no valid pixels")
            work = dem.copy()
            fill_value = float(np.median(work[valid]))
            work[~valid] = fill_value
            pixel_x = abs(src.transform.a)
            pixel_y = abs(src.transform.e)
            dz_dy, dz_dx = np.gradient(work, pixel_y, pixel_x)
            slope = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))
            aspect = (np.degrees(np.arctan2(-dz_dx, dz_dy)) + 360) % 360
            azimuth = np.deg2rad(315.0)
            altitude = np.deg2rad(45.0)
            slope_rad = np.deg2rad(slope)
            aspect_rad = np.deg2rad(aspect)
            hillshade = (
                np.sin(altitude) * np.cos(slope_rad)
                + np.cos(altitude) * np.sin(slope_rad) * np.cos(azimuth - aspect_rad)
            )
            hillshade = np.clip(hillshade * 255, 0, 255)
            for name, array in (("slope", slope), ("aspect", aspect), ("hillshade", hillshade)):
                array = array.astype(np.float32)
                array[~valid] = np.nan
                path = self.processed_dir / f"{name}.tif"
                profile = src.profile.copy()
                profile.update(dtype="float32", nodata=np.nan, compress="deflate")
                with rasterio.open(path, "w", **profile) as dst:
                    dst.write(array, 1)
                outputs[f"{name}_path"] = path
        return TerrainResult(dem_path=dem_path, **outputs)

    def run(self, config: ProjectConfig, overwrite: bool = False) -> TerrainResult:
        sources = self.download_sources(config, overwrite=overwrite)
        dem = self.process_dem(sources, config)
        result = self.derive_terrain(dem, config)
        contour_path = self.derive_contours(dem) if config.layers.contours else None
        result = TerrainResult(
            dem_path=result.dem_path,
            slope_path=result.slope_path,
            aspect_path=result.aspect_path,
            hillshade_path=result.hillshade_path,
            contour_path=contour_path,
        )
        provenance_path = self.write_provenance(config, sources, result)
        return TerrainResult(
            dem_path=result.dem_path,
            slope_path=result.slope_path,
            aspect_path=result.aspect_path,
            hillshade_path=result.hillshade_path,
            contour_path=result.contour_path,
            provenance_path=provenance_path,
        )
