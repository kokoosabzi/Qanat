import pytest

from qanat.config import ProjectConfig


def test_default_location_and_resolution():
    project = ProjectConfig()
    assert project.location.latitude == pytest.approx(36.3916139)
    assert project.location.longitude == pytest.approx(57.6854968)
    assert project.resolution.source_dem_m == 30
    assert project.resolution.output_m == 30


def test_invalid_coordinates_are_rejected():
    with pytest.raises(ValueError):
        ProjectConfig(location={"latitude": 91, "longitude": 57})


def test_upsampling_is_reported_as_a_warning():
    project = ProjectConfig(resolution={"source_dem_m": 30, "output_m": 10})
    assert project.resolution.is_upsampling
    assert any("resampling" in warning for warning in project.warnings())


def test_groundwater_requires_dem():
    with pytest.raises(ValueError):
        ProjectConfig(
            layers={"dem": False},
            analysis={"groundwater": True},
        )
