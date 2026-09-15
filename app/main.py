from __future__ import annotations

import json

import streamlit as st

from qanat.config import ExtentMode, ProjectConfig


def main() -> None:
    st.set_page_config(page_title="Qanat", page_icon="💧", layout="wide")
    st.title("Qanat — Hydrogeospatial Analysis")
    st.caption("Project configuration and investigation planning")

    if "project" not in st.session_state:
        st.session_state.project = ProjectConfig()

    p: ProjectConfig = st.session_state.project

    with st.form("project_config"):
        tabs = st.tabs(
            ["Location", "Extent", "Terrain", "Weather", "Hydrogeology", "Analysis", "Outputs"]
        )

        with tabs[0]:
            c1, c2 = st.columns(2)
            lat = c1.number_input("Latitude", value=p.location.latitude, format="%.7f")
            lon = c2.number_input("Longitude", value=p.location.longitude, format="%.7f")
            name = st.text_input("Project name", value=p.name)

        with tabs[1]:
            mode = st.selectbox("Analysis extent", list(ExtentMode), index=list(ExtentMode).index(p.extent.mode), format_func=lambda x: x.value)
            radius = st.number_input("Radius (m)", min_value=1.0, value=p.extent.radius_m, step=100.0)
            width = st.number_input("Rectangle width (m)", min_value=1.0, value=p.extent.width_m, step=100.0)
            height = st.number_input("Rectangle height (m)", min_value=1.0, value=p.extent.height_m, step=100.0)

        with tabs[2]:
            source_dem = st.number_input("Source DEM resolution (m)", min_value=1.0, value=p.resolution.source_dem_m)
            output_res = st.number_input("Requested output resolution (m)", min_value=1.0, value=p.resolution.output_m)
            st.caption("A finer output grid than the source DEM is resampling; it does not add new terrain information.")
            layer_values = {}
            for field, label in [
                ("dem", "DEM"), ("satellite", "Satellite"), ("slope", "Slope"),
                ("aspect", "Aspect"), ("hillshade", "Hillshade"), ("contours", "Contours"),
                ("flow_direction", "Flow direction"), ("flow_accumulation", "Flow accumulation"),
                ("watersheds", "Watersheds"),
            ]:
                layer_values[field] = st.checkbox(label, value=getattr(p.layers, field))

        with tabs[3]:
            historical_years = st.slider("Historical rainfall period (years)", 1, 100, p.weather.historical_years)
            forecast = st.checkbox("Include forecast", value=p.weather.include_forecast)
            horizon = st.number_input("Forecast horizon (days)", min_value=1, max_value=3650, value=p.weather.forecast_horizon_days)
            drought = st.checkbox("Drought / extremes indicators", value=p.weather.include_drought_indices)
            recharge = st.checkbox("Recharge indicators", value=p.weather.include_recharge_indicators)
            rainfall = st.checkbox("Rainfall", value=p.layers.rainfall)
            soil = st.checkbox("Soil moisture", value=p.layers.soil_moisture)
            et = st.checkbox("Evapotranspiration", value=p.layers.evapotranspiration)

        with tabs[4]:
            geology = st.checkbox("Geology", value=p.layers.geology)
            faults = st.checkbox("Faults / fractures", value=p.layers.faults_fractures)
            wells = st.checkbox("Wells", value=p.layers.wells)
            springs = st.checkbox("Springs", value=p.layers.springs)
            qanats = st.checkbox("Existing qanats", value=p.layers.existing_qanats)

        with tabs[5]:
            terrain_analysis = st.checkbox("Terrain", value=p.analysis.terrain)
            hydro_analysis = st.checkbox("Hydrology", value=p.analysis.hydrology)
            weather_analysis = st.checkbox("Weather / climate", value=p.analysis.weather)
            groundwater = st.checkbox("Groundwater", value=p.analysis.groundwater)
            qanat_candidates = st.checkbox("Qanat candidate zones", value=p.analysis.qanat_candidates)
            tunnel_candidates = st.checkbox("Tunnel candidate corridors", value=p.analysis.tunnel_candidates)

        with tabs[6]:
            maps_2d = st.checkbox("2D maps", value=p.outputs.maps_2d)
            terrain_3d = st.checkbox("3D terrain", value=p.outputs.terrain_3d)
            report = st.checkbox("Evidence report", value=p.outputs.report)
            animation = st.checkbox("Animation", value=p.outputs.animation)
            video = st.checkbox("Video", value=p.outputs.video)

        submitted = st.form_submit_button("Validate and save project")

    if submitted:
        try:
            project = ProjectConfig(
                name=name,
                location={"latitude": lat, "longitude": lon},
                extent={"mode": mode.value, "radius_m": radius, "width_m": width, "height_m": height},
                resolution={"source_dem_m": source_dem, "output_m": output_res},
                layers={**p.layers.model_dump(), **layer_values, "rainfall": rainfall, "soil_moisture": soil, "evapotranspiration": et, "geology": geology, "faults_fractures": faults, "wells": wells, "springs": springs, "existing_qanats": qanats},
                weather={"historical_years": historical_years, "include_forecast": forecast, "forecast_horizon_days": horizon, "include_drought_indices": drought, "include_recharge_indicators": recharge},
                analysis={"terrain": terrain_analysis, "hydrology": hydro_analysis, "weather": weather_analysis, "groundwater": groundwater, "qanat_candidates": qanat_candidates, "tunnel_candidates": tunnel_candidates},
                outputs={"maps_2d": maps_2d, "terrain_3d": terrain_3d, "report": report, "animation": animation, "video": video},
            )
            st.session_state.project = project
            st.success("Project configuration is valid.")
            for warning in project.warnings():
                st.warning(warning)
        except ValueError as exc:
            st.error(str(exc))

    st.divider()
    st.subheader("Project manifest")
    st.code(json.dumps(st.session_state.project.model_dump(mode="json"), indent=2), language="json")
    st.info("Screening results are evidence-ranked candidates, not proof of groundwater or approval for excavation.")


if __name__ == "__main__":
    main()
