import folium
import geopandas as gpd
import pandas as pd
import numpy as np
import pydeck as pdk
import streamlit as st

from folium.plugins import MarkerCluster
from loguru import logger
from plotly.colors import sequential
from pydeck import ViewState


def default_view_states(setting: str = "Canada") -> ViewState:

    if setting == "Canada":
        return ViewState(
            latitude=58,  # Near geographic center of Canada
            longitude=-98,  # Good central longitude
            zoom=3,  # Wide enough to see all provinces
            pitch=10,  # Tilt the map slightly
            bearing=5,  # Slight rotation
        )


def map_ordinal_to_plotly_color(values, palette=None, alpha=140):
    """
    Map ordinal values (like years) to RGBA colors using a Plotly sequential palette.

    Parameters:
        values (list or pd.Series): Ordinal values to map (e.g., years)
        palette (list): List of hex color strings (e.g., plotly.colors.sequential.Viridis)
        alpha (int): Alpha channel (0–255)

    Returns:
        List of RGBA colors as [r, g, b, alpha]
    """
    if palette is None:
        palette = sequential.Viridis

    values = pd.Series(values)
    unique_vals = sorted(values.dropna().unique())
    n_colors = len(palette)

    # Build mapping from unique value to color (loop palette if needed)
    val_to_color = {val: palette[i % n_colors] for i, val in enumerate(unique_vals)}

    def hex_to_rgba(hex_color, alpha):
        hex_color = hex_color.lstrip("#")
        r, g, b = [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]
        return [r, g, b, alpha]

    return [
        hex_to_rgba(val_to_color[v], alpha) if pd.notnull(v) else [150, 150, 150, alpha]
        for v in values
    ]


def make_folium_fire_map(gdf: gpd.GeoDataFrame, zoom_start: float = 5) -> folium.Map:
    # Set default center over Quebec
    m = folium.Map(location=[52.0, -71.0], zoom_start=zoom_start)

    cluster = MarkerCluster().add_to(m)

    for _, row in gdf.iterrows():
        popup = (
            f"🔥 {row.get('fire_name', 'Unknown')}<br>"
            f"Size: {row.get('size_ha', 0):,.1f} ha<br>"
            f"Cause: {row.get('cause_primary', 'N/A')}<br>"
            f"Date: {row.get('report_date', 'Unknown')}"
        )
        folium.CircleMarker(
            location=(row.geometry.y, row.geometry.x),
            radius=4,
            fill=True,
            color="red",
            fill_opacity=0.6,
            popup=folium.Popup(popup, max_width=300),
        ).add_to(cluster)

    return cluster


def make_pydeck_map(
    gdf: gpd.GeoDataFrame,
    color_by_year: bool = False,
    size_by_area: bool = False,
    max_display_radius=5000,
    min_display_radius=300,
    view_state_ref: str = "Canada",
    alpha: int = 140,
) -> pdk.Deck:

    initial_view = default_view_states(setting=view_state_ref)

    df = gdf.copy()
    df["size_ha_fmt"] = df["size_ha"].map("{:,.0f}".format)

    if color_by_year:
        df["fill_color"] = map_ordinal_to_plotly_color(
            df["year"], palette=sequential.Plasma, alpha=140
        )
    else:
        df["fill_color"] = [[255, 0, 0, alpha]] * len(gdf)

    if size_by_area:
        # Square root scale, then normalize
        scaled = np.sqrt(df["size_ha"].clip(0.1, 10000))  # cap at 10,000 ha

        # Normalize to [0, 1]
        scaled = (scaled - scaled.min()) / (scaled.max() - scaled.min())

        # Scale to pixel range
        df["radius"] = (
            scaled * (max_display_radius - min_display_radius) + min_display_radius
        )
    else:
        df["radius"] = 2000

    tooltip = {
        "html": "<b>{fire_name}</b><br/>Size: {size_ha_fmt} ha<br/>Year: {year}<br/>Long.: {longitude} Lat.: {latitude}",
        "style": {"backgroundColor": "steelblue", "color": "white"},
    }

    deck = pdk.Deck(
        initial_view_state=initial_view,
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[longitude, latitude]",
                get_radius="radius",
                get_fill_color="fill_color",
                pickable=True,
            ),
        ],
        tooltip=tooltip,
    )

    return deck
