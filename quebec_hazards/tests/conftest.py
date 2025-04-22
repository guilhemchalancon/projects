import pytest
import geopandas as gpd
import pandas as pd
from shapely import Point


@pytest.fixture
def sample_firepoint_df() -> gpd.GeoDataFrame:
    df = pd.DataFrame(
        [
            {
                "NFDBFIREID": "A001",
                "FIRE_ID": "QC2023_001",
                "FIRENAME": "Rouge",
                "SRC_AGENCY": "SOPFEU",
                "RESPONSE": "Full",
                "YEAR": 2023,
                "MONTH": 6,
                "DAY": 12,
                "REP_DATE": "2023/06/12",
                "ATTK_DATE": "2023/06/13",
                "OUT_DATE": "2023/06/20",
                "ACQ_DATE": "2023/06/25",
                "CAUSE": "Lightning",
                "CAUSE2": None,
                "FIRE_TYPE": "WF",
                "SIZE_HA": 1220.5,
                "PRESCRIBED": False,
                "NAT_PARK": None,
                "PROTZONE": "Z1",
                "MORE_INFO": None,
                "CFS_NOTE1": None,
                "CFS_NOTE2": None,
                "LATITUDE": 48.25,
                "LONGITUDE": -70.1,
            },
            {
                "NFDBFIREID": "A002",
                "FIRE_ID": "QC2023_002",
                "FIRENAME": "Bleu",
                "SRC_AGENCY": "SOPFEU",
                "RESPONSE": "Monitor",
                "YEAR": 2023,
                "MONTH": 7,
                "DAY": 1,
                "REP_DATE": "0000/00/00",
                "ATTK_DATE": "0000/00/00",
                "OUT_DATE": "0000/00/00",
                "ACQ_DATE": "2023-07-15",
                "CAUSE": "Campfire",
                "CAUSE2": None,
                "FIRE_TYPE": "WF",
                "SIZE_HA": 2.0,
                "PRESCRIBED": False,
                "NAT_PARK": "La Mauricie",
                "PROTZONE": "Z2",
                "MORE_INFO": None,
                "CFS_NOTE1": None,
                "CFS_NOTE2": None,
                "LATITUDE": 47.7,
                "LONGITUDE": -72.5,
            },
            {
                "NFDBFIREID": "A003",
                "FIRE_ID": "QC2023_003",
                "FIRENAME": "Vert",
                "SRC_AGENCY": "SOPFEU",
                "RESPONSE": "Full",
                "YEAR": 2023,
                "MONTH": 8,
                "DAY": 5,
                "REP_DATE": "",
                "ATTK_DATE": "",
                "OUT_DATE": "",
                "ACQ_DATE": "",
                "CAUSE": "Debris burning",
                "CAUSE2": None,
                "FIRE_TYPE": "WF",
                "SIZE_HA": 15.0,
                "PRESCRIBED": False,
                "NAT_PARK": None,
                "PROTZONE": "Z3",
                "MORE_INFO": None,
                "CFS_NOTE1": None,
                "CFS_NOTE2": None,
                "LATITUDE": 49.0,
                "LONGITUDE": -71.0,
            },
        ]
    )

    df["geometry"] = df.apply(
        lambda row: Point(row["LONGITUDE"], row["LATITUDE"]), axis=1
    )
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    return gdf
