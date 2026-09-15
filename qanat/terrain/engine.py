from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import rasterio
from pyproj import CRS, Transformer
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import calculate_default_transform, reproject

from qanat.config import ProjectConfig


@dataclass(frozen=True)
class TerrainResult:
    """Paths and metadata produced by the terrain engine."""

    dem_path: Path
    slope_path: Path | None = None
    aspect_path: Path | None = None
    hillshade_path: Path | None = None


class TerrainEngine:
    """Acquire a source DEM and produce a projected, clipped analysis DEM.

    The first implementation deliberately keeps acquisition deterministic and
    dependency-light: Copernicus GLO-30 Public is read from its public S3 COG
    endpoint. Processing is performed locally with Rasterio/PROJ.
    """

    SOURCE_TEMPLATE = (
        "https://copernicus-dem-30m.s3.amazonaws.com/"
        "Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM/"
        "Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM.tif"
    )

    def __init__(self, data_root: str | Path = "data") -> None:
        self.data_root = Path(data_root)
        self.raw_dir = self.data_root / "raw" / "dem"
        self.processed_dir = self.data_root / "processed" / "terrain"

    @staticmethod
    def _tile_indices(latitude: float, longitude: float) -> tuple[int, int]:
        if latitude < 0 or longitude < 0:
            raise ValueError("The initial Copernicus downloader supports northern/eastern tiles only")
        return int(np.floor(latitude)), int(np.floor(longitude))

    @classmethod
    def tile_url(cls, latitude: float, longitude: float) -> str:
        lat, lon = cls._tile_indices(latitude, longitude)
        return cls.SOURCE_TEMPLATE.format(lat=lat, lon=lon)

    def download_source(self, config: ProjectConfig, overwrite: bool = False) -> Path:
        """Download the 1-degree Copernicus GLO-30 COG containing the target."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        lat, lon = self._tile_indices(config.location.latitude, config.location.longitude)
        destination = self.raw_dir / f"copernicus_N{lat:02d}_E{lon:03d}_30m.tif"
        if destination.exists() and not overwrite:
            return destination

        url = self.tile_url(config.location.latitude, config.location.longitude)
        try:
            with urlopen(url, timeout=120) as response, destination.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return destination

    @staticmethod
    def _utm_crs(latitude: float, longitude: float) -> CRS:
        zone = int((longitude + 180) // 6) + 1
        epsg = 32600 + zone if latitude >= 0 else 32700 + zone
        return CRS.from_epsg(epsg)

    @staticmethod
    def _analysis_window(config: ProjectConfig) -> tuple[float, float, float, float]:
        """Return lon/lat bounds around the configured point.

        Radius mode is converted using a local metre-per-degree approximation.
        The final clip happens after reprojection in metres, so this bounds only
        controls how much source data is read.
        """
        lat = config.location.latitude
        lon = config.location.longitude
        if config.extent.mode.value == "radius":
            half_w = config.extent.radius_m / (111_320 * max(np.cos(np.deg2rad(lat)), 0.1))
            half_h = config.extent.radius_m / 110_540
        else:
            half_w = config.extent.width_m / (2 * 111_320 * max(np.cos(np.deg2rad(lat)), 0.1))
            half_h = config.extent.height_m / (2 * 110_540)
        return lon - half_w, lat - half_h, lon + half_w, lat + half_h

    def process_dem(self, source_path: str | Path, config: ProjectConfig) -> Path:
        """Reproject, resample and clip a source DEM to the analysis extent."""
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.processed_dir / "dem.tif"
        dst_crs = self._utm_crs(config.location.latitude, config.location.longitude)
        left, bottom, right, top = self._analysis_window(config)

        with rasterio.open(source_path) as src:
            # Read the geographic source window first to avoid warping the whole tile.
            window = rasterio.windows.from_bounds(left, bottom, right, top, src.transform)
            window = window.round_offsets().round_lengths()
            window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
            if window.width <= 0 or window.height <= 0:
                raise ValueError("Configured analysis extent does not overlap the source DEM")
            data = src.read(1, window=window, masked=True)
            src_transform = src.window_transform(window)
            src_nodata = src.nodata if src.nodata is not None else -9999.0

            transform, width, height = calculate_default_transform(
                src.crs,
                dst_crs,
                data.shape[1],
                data.shape[0],
                *rasterio.windows.bounds(window, src.transform),
                resolution=config.resolution.output_m,
            )
            destination = np.full((height, width), src_nodata, dtype=np.float32)
            reproject(
                source=data.filled(src_nodata).astype(np.float32),
                destination=destination,
                src_transform=src_transform,
                src_crs=src.crs,
                src_nodata=src_nodata,
                dst_transform=transform,
                dst_crs=dst_crs,
                dst_nodata=src_nodata,
                resampling=Resampling.bilinear,
            )

            profile = src.profile.copy()
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
        """Mask pixels outside a metric radius without flattening index arrays.

        This is intentionally a separate method because a previous implementation
        used ``rasterio.transform.xy`` with 2-D indices and produced flattened
        coordinate arrays, causing a boolean-index shape mismatch.
        """
        xs, ys = cls._metric_grid(transform, array.shape)
        inside = (xs - center_x) ** 2 + (ys - center_y) ** 2 <= radius_m**2
        result = array.copy()
        result[~inside] = np.nan
        return result

    def derive_terrain(self, dem_path: str | Path, config: ProjectConfig) -> TerrainResult:
        """Generate slope, aspect and hillshade rasters from the processed DEM."""
        dem_path = Path(dem_path)
        outputs: dict[str, Path | None] = {"slope_path": None, "aspect_path": None, "hillshade_path": None}
        with rasterio.open(dem_path) as src:
            dem = src.read(1).astype(np.float32)
            nodata = src.nodata
            valid = np.isfinite(dem) if nodata is None else dem != nodata
            if not valid.any():
                raise ValueError("DEM contains no valid pixels")
            work = dem.copy()
            fill_value = float(np.nanmedian(work[valid]))
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
        source = self.download_source(config, overwrite=overwrite)
        dem = self.process_dem(source, config)
        return self.derive_terrain(dem, config)
