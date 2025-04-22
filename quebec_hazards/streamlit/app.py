import geopandas as gpd
import importlib
import streamlit as st

from datetime import date
from hazards.src.components import fires
from hazards.src.visuals import maps

importlib.reload(maps)


@st.cache_data(show_spinner=True)
def load_fires() -> gpd.GeoDataFrame:
    loader = fires.FirePointDataLoader()
    loader.load()
    return loader.data.drop(columns="geometry")


def main():
    from components.page_config import get_page_config

    get_page_config()
    st.title("Canadian Fires")

    gdf = load_fires()

    st.dataframe(gdf.head())

    min_date = gdf["report_date"].dropna().min()
    max_date = gdf["report_date"].dropna().max()

    cell_1_1, cell_1_2, cell_1_3 = st.columns([6, 3, 3], border=True)

    with cell_1_1:
        selected_date = st.slider(
            label="Date picker",
            help="Show fires reported on or after the selected date.",
            min_value=min_date,
            max_value=max_date,
            value=date(2020, 1, 1),
        )

    with cell_1_2:
        color_by_year = st.checkbox("Color by year", value=False)

    with cell_1_3:
        size_by_area = st.checkbox("Scale by fire size", value=True)

    filtered = gdf[gdf["report_date"] >= selected_date]
    st.write(
        f"Showing {len(filtered):,} fires reported since {selected_date.strftime("%A %d %B %Y")}"
    )

    deck = maps.make_pydeck_map(
        filtered[["longitude", "latitude", "fire_name", "size_ha", "year"]],
        color_by_year=color_by_year,
        size_by_area=size_by_area,
    )
    st.pydeck_chart(deck)


if __name__ == "__main__":

    main()
