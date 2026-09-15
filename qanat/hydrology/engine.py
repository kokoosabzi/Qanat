from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.transform import xy


@dataclass(frozen=True)
class HydrologyResult:
    """Paths to raster/vector hydrology artifacts."""

    flow_direction_path: Path
    flow_accumulation_path: Path
    drainage_path: Path
    drainage_network_path: Path | None = None
    stream_order_path: Path | None = None
    watershed_path: Path | None = None


class HydrologyEngine:
    """Deterministic raster hydrology using an 8-neighbour D8 model."""

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
            src_r0, src_r1 = max(0, -dr), min(rows, rows - dr)
            src_c0, src_c1 = max(0, -dc), min(cols, cols - dc)
            dst_r0, dst_r1 = max(0, dr), min(rows, rows + dr)
            dst_c0, dst_c1 = max(0, dc), min(cols, cols + dc)
            source = elevation[src_r0:src_r1, src_c0:src_c1]
            target = elevation[dst_r0:dst_r1, dst_c0:dst_c1]
            source_valid = valid_mask[src_r0:src_r1, src_c0:src_c1]
            target_valid = valid_mask[dst_r0:dst_r1, dst_c0:dst_c1]
            drop = source - target
            current_best = best_drop[src_r0:src_r1, src_c0:src_c1]
            better = source_valid & target_valid & (drop > current_best)
            best_drop[src_r0:src_r1, src_c0:src_c1] = np.where(better, drop, current_best)
            current_direction = direction[src_r0:src_r1, src_c0:src_c1]
            direction[src_r0:src_r1, src_c0:c src_c1] = current_direction
            direction[src_r0:src_r1, src_c0:src_c1] = np.where(better, code, current_direction)
        direction[~valid_mask] = 0
        return direction

    @classmethod
    def flow_accumulation(cls, flow_direction: np.ndarray, valid: np.ndarray | None = None) -> np.ndarray:
        direction = np.asarray(flow_direction, dtype=np.uint8)
        if direction.ndim != 2:
            raise ValueError("flow direction must be a 2D array")
        valid_mask = direction != 0 if valid is None else np.asarray(valid, dtype=bool)
        if valid_mask.shape != direction.shape:
            raise ValueError("valid mask must match flow direction shape")
        rows, cols = direction.shape
        accumulation = np.zeros(direction.shape, dtype=np.float64)
        accumulation[valid_mask] = 1.0
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
            nr, nc = receivers[r, c]
            if nr < 0:
                continue
            accumulation[nr, nc] += accumulation[r, c]
            indegree[nr, nc] -= 1
            if indegree[nr, nc] == 0:
                queue.append((int(nr), int(nc)))
        return accumulation

    @staticmethod
    def select_outlet(flow_accumulation: np.ndarray) -> tuple[int, int]:
        accumulation = np.asarray(flow_accumulation, dtype=float)
        if accumulation.ndim != 2:
            raise ValueError("flow accumulation must be a 2D array")
        valid = np.isfinite(accumulation)
        if not valid.any():
            raise ValueError("flow accumulation contains no finite cells")
        masked = np.where(valid, accumulation, -np.inf)
        row, col = np.unravel_index(np.argmax(masked), masked.shape)
        if not np.isfinite(masked[row, col]) or masked[row, col] <= 0:
            raise ValueError("flow accumulation contains no positive cell")
        return int(row), int(col)

    @classmethod
    def stream_order(
        cls,
        flow_direction: np.ndarray,
        flow_accumulation: np.ndarray,
        threshold_cells: int = 1,
        valid: np.ndarray | None = None,
    ) -> np.ndarray:
        """Return Strahler stream order for the thresholded D8 stream graph."""
        if threshold_cells < 1:
            raise ValueError("threshold_cells must be at least 1")
        direction = np.asarray(flow_direction, dtype=np.uint8)
        accumulation = np.asarray(flow_accumulation, dtype=float)
        if direction.shape != accumulation.shape:
            raise ValueError("flow direction and accumulation shapes must match")
        valid_mask = np.isfinite(accumulation) if valid is None else np.asarray(valid, dtype=bool)
        if valid_mask.shape != direction.shape:
            raise ValueError("valid mask must match flow direction shape")
        stream = valid_mask & (direction != 0) & (accumulation >= threshold_cells)
        order = np.zeros(direction.shape, dtype=np.uint8)
        code_to_delta = {code: (dr, dc) for dr, dc, code in cls._D8}
        incoming: dict[tuple[int, int], list[tuple[int, int]]] = {tuple(idx): [] for idx in zip(*np.nonzero(stream))}
        indegree = {cell: 0 for cell in incoming}
        receiver: dict[tuple[int, int], tuple[int, int] | None] = {}
        rows, cols = direction.shape
        for r, c in incoming:
            delta = code_to_delta.get(int(direction[r, c]))
            if delta is None:
                receiver[(r, c)] = None
                continue
            nr, nc = r + delta[0], c + delta[1]
            if 0 <= nr < rows and 0 <= nc < cols and stream[nr, nc]:
                receiver[(r, c)] = (nr, nc)
                incoming[(nr, nc)].append((r, c))
                indegree[(nr, nc)] += 1
            else:
                receiver[(r, c)] = None
        queue = [cell for cell, degree in indegree.items() if degree == 0]
        head = 0
        while head < len(queue):
            cell = queue[head]
            head += 1
            upstream = [int(order[src]) for src in incoming[cell] if order[src] > 0]
            order[cell] = 1 if not upstream else (max(upstream) + 1 if upstream.count(max(upstream)) >= 2 else max(upstream))
            target = receiver[cell]
            if target is not None:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
        return order

    @classmethod
    def delineate_watershed(
        cls,
        flow_direction: np.ndarray,
        outlet_row: int,
        outlet_col: int,
        valid: np.ndarray | None = None,
    ) -> np.ndarray:
        direction = np.asarray(flow_direction, dtype=np.uint8)
        if direction.ndim != 2:
            raise ValueError("flow direction must be a 2D array")
        rows, cols = direction.shape
        if not (0 <= outlet_row < rows and 0 <= outlet_col < cols):
            raise ValueError("outlet cell is outside flow-direction raster")
        valid_mask = direction != 0 if valid is None else np.asarray(valid, dtype=bool)
        if valid_mask.shape != direction.shape:
            raise ValueError("valid mask must match flow direction shape")
        if not valid_mask[outlet_row, outlet_col]:
            raise ValueError("outlet cell is not valid")
        code_to_delta = {code: (dr, dc) for dr, dc, code in cls._D8}
        watershed = np.zeros(direction.shape, dtype=bool)
        watershed[outlet_row, outlet_col] = True
        queue = [(outlet_row, outlet_col)]
        head = 0
        while head < len(queue):
            receiver_row, receiver_col = queue[head]
            head += 1
            for source_row in range(max(0, receiver_row - 1), min(rows, receiver_row + 2)):
                for source_col in range(max(0, receiver_col - 1), min(cols, receiver_col + 2)):
                    if watershed[source_row, source_col] or not valid_mask[source_row, source_col]:
                        continue
                    delta = (receiver_row - source_row, receiver_col - source_col)
                    candidate_code = code_to_delta
                    candidate_code = next((code for code, code_delta in candidate_code.items() if code_delta == delta), None)
                    if candidate_code is not None and int(direction[source_row, source_col]) == candidate_code:
                        watershed[source_row, source_col] = True
                        queue.append((source_row, source_col))
        return watershed

    @classmethod
    def drainage_network_geojson(
        cls,
        flow_direction: np.ndarray,
        flow_accumulation: np.ndarray,
        transform,
        crs,
        threshold_cells: int,
        valid: np.ndarray | None = None,
    ) -> dict:
        if threshold_cells < 1:
            raise ValueError("threshold_cells must be at least 1")
        direction = np.asarray(flow_direction, dtype=np.uint8)
        accumulation = np.asarray(flow_accumulation, dtype=float)
        if direction.shape != accumulation.shape:
            raise ValueError("flow direction and accumulation shapes must match")
        valid_mask = direction != 0 if valid is None else np.asarray(valid, dtype=bool)
        if valid_mask.shape != direction.shape:
            raise ValueError("valid mask must match flow direction shape")
        if crs is None:
            raise ValueError("a CRS is required for drainage vectorization")
        transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        code_to_delta = {code: (dr, dc) for dr, dc, code in cls._D8}
        features = []
        rows, cols = direction.shape
        for r, c in zip(*np.nonzero(valid_mask & (accumulation >= threshold_cells))):
            delta = code_to_delta.get(int(direction[r, c]))
            if delta is None:
                continue
            nr, nc = r + delta[0], c + delta[1]
            if not (0 <= nr < rows and 0 <= nc < cols) or not valid_mask[nr, nc]:
                continue
            x1, y1 = xy(transform, r, c, offset="center")
            x2, y2 = xy(transform, nr, nc, offset="center")
            lon1, lat1 = transformer.transform(x1, y1)
            lon2, lat2 = transformer.transform(x2, y2)
            features.append({
                "type": "Feature",
                "properties": {"accumulation_cells": float(accumulation[r, c]), "d8_code": int(direction[r, c])},
                "geometry": {"type": "LineString", "coordinates": [[lon1, lat1], [lon2, lat2]]},
            })
        return {"type": "FeatureCollection", "name": "qanat_drainage_network", "features": features}

    @staticmethod
    def drainage_mask(flow_accumulation: np.ndarray, threshold_cells: int = 1) -> np.ndarray:
        if threshold_cells < 1:
            raise ValueError("threshold_cells must be at least 1")
        accumulation = np.asarray(flow_accumulation, dtype=float)
        return np.isfinite(accumulation) & (accumulation >= threshold_cells)

    def run(
        self,
        dem_path: str | Path,
        threshold_cells: int = 10,
        outlet_row: int | None = None,
        outlet_col: int | None = None,
    ) -> HydrologyResult:
        dem_path = Path(dem_path)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        with rasterio.open(dem_path) as src:
            dem = src.read(1).astype(np.float64)
            nodata = src.nodata
            valid = np.isfinite(dem) if nodata is None else np.isfinite(dem) & (dem != nodata)
            direction = self.flow_direction(dem, valid)
            accumulation = self.flow_accumulation(direction, valid)
            drainage = self.drainage_mask(accumulation, threshold_cells)
            stream_order = self.stream_order(direction, accumulation, threshold_cells, valid)
            profile = src.profile.copy()
            flow_direction_path = self.processed_dir / "flow_direction.tif"
            flow_accumulation_path = self.processed_dir / "flow_accumulation.tif"
            drainage_path = self.processed_dir / "drainage.tif"
            drainage_network_path = self.processed_dir / "drainage_network.geojson"
            stream_order_path = self.processed_dir / "stream_order.tif"

            with rasterio.open(flow_direction_path, "w", **{**profile, "dtype": "uint8", "count": 1, "nodata": 0, "compress": "deflate"}) as dst:
                dst.write(direction, 1)
                dst.set_band_description(1, "d8_direction")
            with rasterio.open(flow_accumulation_path, "w", **{**profile, "dtype": "float32", "count": 1, "nodata": 0, "compress": "deflate"}) as dst:
                output = accumulation.astype(np.float32)
                output[~valid] = 0
                dst.write(output, 1)
                dst.set_band_description(1, "upstream_cell_count")
            with rasterio.open(drainage_path, "w", **{**profile, "dtype": "uint8", "count": 1, "nodata": 0, "compress": "deflate"}) as dst:
                output = np.where(drainage & valid, 1, 0).astype(np.uint8)
                dst.write(output, 1)
                dst.set_band_description(1, f"drainage_threshold_{threshold_cells}_cells")
            with rasterio.open(stream_order_path, "w", **{**profile, "dtype": "uint8", "count": 1, "nodata": 0, "compress": "deflate"}) as dst:
                dst.write(stream_order, 1)
                dst.set_band_description(1, "strahler_stream_order")

            network = self.drainage_network_geojson(direction, accumulation, src.transform, src.crs, threshold_cells, valid)
            drainage_network_path.write_text(json.dumps(network, ensure_ascii=False), encoding="utf-8")

            if (outlet_row is None) != (outlet_col is None):
                raise ValueError("outlet_row and outlet_col must be provided together")
            if outlet_row is None and outlet_col is None:
                outlet_row, outlet_col = self.select_outlet(accumulation)

            watershed = self.delineate_watershed(direction, outlet_row, outlet_col, valid)
            watershed_path = self.processed_dir / "watershed.tif"
            with rasterio.open(watershed_path, "w", **{**profile, "dtype": "uint8", "count": 1, "nodata": 0, "compress": "deflate"}) as dst:
                dst.write(watershed.astype(np.uint8), 1)
                dst.set_band_description(1, "watershed_mask")

        return HydrologyResult(flow_direction_path, flow_accumulation_path, drainage_path, drainage_network_path, stream_order_path, watershed_path)
