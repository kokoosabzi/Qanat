from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ExtentMode(str, Enum):
    RADIUS = "radius"
    RECTANGLE = "rectangle"
    POLYGON = "polygon"


class Location(BaseModel):
    latitude: float = 36.3916139
    longitude: float = 57.6854968

    @field_validator("latitude")
    @classmethod
    def latitude_range(cls, value: float) -> float:
        if not -90 <= value <= 90:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def longitude_range(cls, value: float) -> float:
        if not -180 <= value <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return value


class Extent(BaseModel):
    mode: ExtentMode = ExtentMode.RADIUS
    radius_m: float = Field(default=5000, gt=0)
    width_m: float = Field(default=10000, gt=0)
    height_m: float = Field(default=10000, gt=0)
    polygon_geojson: dict | None = None


class Resolution(BaseModel):
    source_dem_m: float = Field(default=30, gt=0)
    output_m: float = Field(default=30, gt=0)

    @property
    def is_upsampling(self) -> bool:
        return self.output_m < self.source_dem_m


class Layers(BaseModel):
    dem: bool = True
    satellite: bool = True
    slope: bool = True
    aspect: bool = True
    hillshade: bool = True
    contours: bool = True
    flow_direction: bool = True
    flow_accumulation: bool = True
    watersheds: bool = True
    geology: bool = False
    faults_fractures: bool = False
    wells: bool = False
    springs: bool = False
    existing_qanats: bool = False
    rainfall: bool = True
    soil_moisture: bool = True
    evapotranspiration: bool = True


class WeatherConfig(BaseModel):
    historical_years: int = Field(default=20, ge=1, le=100)
    include_forecast: bool = True
    forecast_horizon_days: int = Field(default=180, ge=1, le=3650)
    include_drought_indices: bool = True
    include_recharge_indicators: bool = True


class AnalysisConfig(BaseModel):
    terrain: bool = True
    hydrology: bool = True
    weather: bool = True
    groundwater: bool = True
    qanat_candidates: bool = True
    tunnel_candidates: bool = False


class OutputConfig(BaseModel):
    maps_2d: bool = True
    terrain_3d: bool = True
    report: bool = True
    animation: bool = False
    video: bool = False


class ProjectConfig(BaseModel):
    name: str = "default_qanat_project"
    location: Location = Field(default_factory=Location)
    extent: Extent = Field(default_factory=Extent)
    resolution: Resolution = Field(default_factory=Resolution)
    layers: Layers = Field(default_factory=Layers)
    weather: WeatherConfig = Field(default_factory=WeatherConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    outputs: OutputConfig = Field(default_factory=OutputConfig)

    @model_validator(mode="after")
    def validate_analysis_dependencies(self) -> "ProjectConfig":
        if self.analysis.groundwater and not self.layers.dem:
            raise ValueError("groundwater analysis requires the DEM layer")
        if self.analysis.weather and not self.layers.rainfall:
            raise ValueError("weather analysis requires the rainfall layer")
        return self

    def warnings(self) -> list[str]:
        messages: list[str] = []
        if self.resolution.is_upsampling:
            messages.append(
                "Output resolution is finer than the source DEM. This is resampling, "
                "not creation of new terrain information."
            )
        if self.analysis.groundwater and not any(
            [self.layers.geology, self.layers.wells, self.layers.springs]
        ):
            messages.append(
                "Groundwater analysis has no geology, wells, or springs selected; "
                "results should be treated as low-evidence screening only."
            )
        return messages
