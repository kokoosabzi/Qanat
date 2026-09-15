from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio


@dataclass(frozen=True)
class HydrologyResult:
    """Paths to raster hydrology artifacts."""

    flow_direction_path: Path
    flow_accumulation_path: Path
    drainage_path: Path


class HydrologyEngine:
    """Deterministic raster hydrology using an 8-neighbour D8 model."""

    # ESRI-style D8 codes: E, SE, S, SW, W, NW, N, NE.
    _D8 = (
        (0, 1, 1),
        (1, 1, 2),
        (1, 0, 4),
        (1, -1, 8),
        (0, -1, 16),
        (-1, -1, 32),
        (-1, 0, 64),
        (-1, 1, 128),
    )

    def __init__(self, data_root: str | Path = "data") -> None:
        self.data_root = Path(data_root)
        self.processed_dir = self.data_root / "processed" / "hydrology"

    @classmethod
    def flow_direction(cls, dem: np.ndarray, valid: np.ndarray | None = None) -> np.ndarray:
        """Return D8 flow-direction codes; zero means sink/edge/no-data."""
        elevation = np.asarray(dem, dtype=float)
        if elevation.ndim != 2:
            raise ValueError("DEM must be a 2D array")
        valid_mask = np.isfinite(elevation) if valid is None else np.asarray(valid, dtype=bool)
        if valid_mask.shape != elevation.shape:
            raise ValueError("valid mask must match DEM shape")

        rows, cols = elevation.shape
        direction = np.zeros(elevation.shape, dtype=np.uint8)
        best_drop = np.zeros(elevation.shape, dtype=float)

        for dr, dc, code in cls._D8:
            src_r0 = max(0, -dr)
            src_r1 = min(rows, rows - dr)
            src_c0 = max(0, -dc)
            src_c1 = min(cols, cols - dc)
            dst_r0 = max(0, dr)
            dst_r1 = min(rows, rows + dr)
            dst_c0 = max(0, dc)
            dst_c1 = min(cols, cols + dc)

            source = elevation[src_r0:src_r1, src_c0:src_c1]
            target = elevation[dst_r0:dst_r1, dst_c0:dst_c1]
            source_valid = valid_mask[src_r0:src_r1, src_c0:src_c1]
            target_valid = valid_mask[dst_r0:dst_r1, dst_c0:dst_c1]
            drop = source - target
            better = source_valid & target_valid & (drop > best_drop[src_r0:src_r1, src_c0:src_c1])
            best_drop[src_r0:src_r1, src_c0:src_c1] = np.where(better, drop, best_drop[src_r0:src_r1, src_c0:src_c1])
            direction[src_r0:src_r1, src_c0:src_c1] = np.where(
                better,
                code,
                direction[src_r0:src_r1, src_c0:src_c1],
            )

        direction[~valid_mask] = 0
        return direction

    @classmethod
    def flow_accumulation(
        cls,
        flow_direction: np.ndarray,
        valid: np.ndarray | None = None,
    ) -> np.ndarray:
        """Return upstream cell counts including each source cell itself."""
        direction = np.asarray(flow_direction, dtype=np.uint8)
        if direction.ndim != 2:
            raise ValueError("flow direction must be a 2D array")
        valid_mask = direction != 0 if valid is None else np.asarray(valid, dtype=bool)
        if valid_mask.shape != direction.shape:
            raise ValueError("valid mask must match flow direction shape")

        rows, cols = direction.shape
        accumulation = np.zeros(direction.shape, dtype=np.float64)
        accumulation[valid_mask] = 1.0

        # Process high-to-low terrain order independently of elevation.
        # The D8 graph has already encoded downhill direction, so repeated
        # propagation in topological order is unnecessary for acyclic DEMs.
        indegree = np.zeros(direction.shape, dtype=np.int32)
        receivers = np.full(direction.shape + (2,), -1, dtype=np.int32)

        code_to_delta = {code: (dr, dc) for dr, dc, code in cls._D8}
        for r, c in zip(*np.nonzero(valid_mask)):
            delta = code_to_delta.get(int(direction[r, c]))
            if delta is None:
                continue
            nr, nc = r + delta[0], c + delta[1]
            if 0 <= nr < rows and 0 <= nc < cols and valid_mask[nr, nc]:
                receivers[r, c] = (nr, nc)
                indegree[nr, nc] += 1

        queue = [tuple(idx) for idx in zip(*np.nonzero(valid_mask & (indegree == 0)))]
        head = 0
        while head < len(queue):
            r, c = queue[head]
            head += 1
            receiver = receivers[r, c]
            nr, nc = receiver
            if nr < 0:
                continue
            accumulation[nr, nc] += accumulation[r, c]
            indegree[nr, nc] -= 1
            if indegree[nr, nc] == 0:
                queue.append((int(nr), int(nc)))

        return accumulation

    @staticmethod
    def drainage_mask(flow_accumulation: np.ndarray, threshold_cells: int = 1) -> np.ndarray:
        """Classify drainage cells from an accumulation threshold."""
        if threshold_cells < 1:
            raise ValueError("threshold_cells must be at least 1")
        accumulation = np.asarray(flow_accumulation, dtype=float)
        return np.isfinite(accumulation) & (accumulation >= threshold_cells)

    def run(self, dem_path: str | Path, threshold_cells: int = 10) -> HydrologyResult:
        """Read a DEM, compute D8 artifacts and write GeoTIFF outputs."""
        dem_path = Path(dem_path)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        with rasterio.open(dem_path) as src:
            dem = src.read(1).astype(np.float64)
            nodata = src.nodata
            valid = np.isfinite(dem) if nodata is None else np.isfinite(dem) & (dem != nodata)
            direction = self.flow_direction(dem, valid)
            accumulation = self.flow_accumulation(direction, valid)
            drainage = self.drainage_mask(accumulation, threshold_cells)

            profile = src.profile.copy()
            flow_direction_path = self.processed_dir / "flow_direction.tif"
            flow_accumulation_path = self.processed_dir / "flow_accumulation.tif"
            drainage_path = self.processed_dir / "drainage.tif"

            with rasterio.open(
                flow_direction_path,
                "w",
                **{**profile, "dtype": "uint8", "count": 1, "nodata": 0, "compress": "deflate"},
            ) as dst:
                dst.write(direction, 1)
                dst.set_band_description(1, "d8_direction")

            with rasterio.open(
                flow_accumulation_path,
                "w",
                **{**profile, "dtype": "float32", "count": 1, "nodata": 0, "compress": "deflate"},
            ) as dst:
                output = accumulation.astype(np.float32)
                output[~valid] = 0
                dst.write(output, 1)
                dst.set_band_description(1, "upstream_cell_count")

            with rasterio.open(
                drainage_path,
                "w",
                **{**profile, "dtype": "uint8", "count": 1, "nodata": 0, "compress": "deflate"},
            ) as dst:
                output = np.where(drainage & valid, 1, 0).astype(np.uint8)
                dst.write(output, 1)
                dst.set_band_description(1, f"drainage_threshold_{threshold_cells}_cells")

        return HydrologyResult(
            flow_direction_path=flow_direction_path,
            flow_accumulation_path=flow_accumulation_path,
            drainage_path=drainage_path,
        )
