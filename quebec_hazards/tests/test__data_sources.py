import pytest
import geopandas as gpd

from hazards.src.components.fires import FirePointDataLoader


def test__firedataloader():
    fdl = FirePointDataLoader()
    assert isinstance(fdl, FirePointDataLoader)


def test__firedataloader_validation(sample_firepoint_df):
    fdl = FirePointDataLoader()
    validated_df, pass_rate = fdl.validate(gdf=sample_firepoint_df)

    assert isinstance(validated_df, gpd.GeoDataFrame)
    assert len(validated_df) > 0
    assert pass_rate == 1


def test__firedataloader__loading_with_no_validation():
    fdl = FirePointDataLoader()
    fdl.load(validate=False)

    assert isinstance(fdl.data, gpd.GeoDataFrame)
    assert len(fdl.data) > 0


def test__firedataloader__loading_with_validation():
    fdl = FirePointDataLoader()
    fdl.load(validate=True)

    assert isinstance(fdl.data, gpd.GeoDataFrame)
    assert len(fdl.data) > 0
