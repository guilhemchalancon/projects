import geopandas as gpd
import io
import pandas as pd
import requests
import tempfile
import zipfile

from datetime import date, datetime
from loguru import logger
from pathlib import Path
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
    ValidationError,
)
from shapely import Point
from typing import List, Optional
from typing import List, Union, Optional, Tuple, Type


class FirePoint(BaseModel):
    """
    National Fire Database
    """

    nfdb_fire_id: Optional[str] = Field(
        None, alias="NFDBFIREID", description="NFDB unique identifier"
    )
    fire_id: Optional[str] = Field(None, alias="FIRE_ID", description="Local fire ID")
    fire_name: Optional[str] = Field(
        None, alias="FIRENAME", description="Fire name if known"
    )

    src_agency: Optional[str] = Field(
        None,
        alias="SRC_AGENCY",
        description="Agency (province, territory, parks) from which the fire data has been obtained.",
    )
    agency_response: Optional[str] = Field(
        None,
        alias="RESPONSE",
        description="Response type. Standard classes include FUL-Full response, MOD-Modified response, MON-Monitored. Additional values may be used by some agencies, and over time.",
    )

    year: int = Field(
        ...,
        alias="YEAR",
        description="Year of fire as provided by individual agencies. Note1: -999 = unknown year. Note2: Some agency source data record their fires using fiscal year, however the NFDB 'year' field represents calendar year, derived from REP_DATE",
    )
    month: int = Field(..., alias="MONTH")
    day: Optional[int] = Field(None, alias="DAY")

    ignition_date: Optional[date] = Field(
        None, alias="ATTK_DATE", description="Date fire attack began"
    )
    report_date: Optional[date] = Field(
        None, alias="REP_DATE", description="Date fire was reported"
    )
    out_date: Optional[date] = Field(
        None, alias="OUT_DATE", description="Date fire was declared out"
    )
    acq_date: Optional[date] = Field(
        None, alias="ACQ_DATE", description="Date data was acquired"
    )

    cause_primary: Optional[str] = Field(
        None,
        alias="CAUSE",
        description="General cause of fire as reported by agency. N-Natural/Lightning caused; H-Human caused; H-PB Human prescribed burn; U-Unknown/undetermined cause.",
    )
    cause_secondary: Optional[str] = Field(
        None, alias="CAUSE2", description="Secondary cause (if known)"
    )
    fire_type: Optional[str] = Field(
        None, alias="FIRE_TYPE", description="Type of fire (wildfire, etc.)"
    )

    size_ha: Optional[float] = Field(
        None, alias="SIZE_HA", description="Size in hectares"
    )
    prescribed: Optional[bool] = Field(
        None, alias="PRESCRIBED", description="Was it a prescribed fire?"
    )
    national_park: Optional[str] = Field(
        None, alias="NAT_PARK", description="Name of national park if in one"
    )
    protection_zone: Optional[str] = Field(
        None,
        alias="PROTZONE",
        description="Protection Zone as indicated by source agency. There is currently no official national standard that has been applied to this attribute.",
    )

    more_info: Optional[str] = Field(None, alias="MORE_INFO")
    note1: Optional[str] = Field(None, alias="CFS_NOTE1")
    note2: Optional[str] = Field(None, alias="CFS_NOTE2")

    latitude: float = Field(..., alias="LATITUDE")
    longitude: float = Field(..., alias="LONGITUDE")
    location: Optional[Tuple[float, float]] = Field(None, description="(lat, lon)")

    @field_validator("prescribed", mode="before")
    @classmethod
    def parse_boolean(cls, v):
        if isinstance(v, (bool)):
            return v
        if not v:
            return None
        if str(v).strip() in {"PB"}:
            return True
        return None

    @field_validator(
        "report_date", "ignition_date", "out_date", "acq_date", mode="before"
    )
    @classmethod
    def parse_dates(cls, v):
        if isinstance(v, (date, datetime)):
            return v
        if not v or str(v).strip() in {"", "0000/00/00", "0000-00-00"}:
            return None
        for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(v, fmt).date()
            except ValueError:
                continue
        return None

    @model_validator(mode="after")
    def set_location(self):
        if self.location is None:
            if self.latitude is None or self.longitude is None:
                raise ValueError("Missing latitude or longitude to build location")
            self.location = (self.latitude, self.longitude)
        return self

    def __str__(self):
        return f"🔥 {self.fire_id or 'N/A'} on {self.ignition_date or f'{self.year}-{self.month:02d}'} — {self.size_ha or 0:.1f} ha"

    model_config = ConfigDict(
        validate_by_name=True,
        extra="ignore",
    )


class FirePointDataLoader:
    """
    Basic data fire loader based on the Canadian National Fire Database (CNFDB)

    Notes
    -----
    The Canadian National Fire Database (CNFDB) fire point data is
    a collection of forest fire locations as provided by Canadian fire
    management agencies including provinces, territories, and Parks Canada.

    Time period
    -----------
    From:1959 - To:2023

    Maintenance and update frequency
    --------------------------------
    Annually
    """

    DATA_URL = "https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point.zip"

    def __init__(
        self,
    ):
        self.gdf: Optional[gpd.GeoDataFrame] = None
        self.model: Type[BaseModel] = FirePoint

    def _download_and_extract(self) -> gpd.GeoDataFrame:
        """
        Download the ZIP archive into memory, finds the .shp
        file and reads it into a geopandas dataframe.
        """
        logger.info("📥 Downloading wildfire data from Canadian NFDB...")

        r = requests.get(self.DATA_URL)
        r.raise_for_status()
        zip_bytes = io.BytesIO(r.content)

        with tempfile.TemporaryDirectory() as tmpdir:
            z = zipfile.ZipFile(zip_bytes)
            z.extractall(tmpdir)
            shp_path = next(Path(tmpdir).rglob("*.shp"))
            logger.info(f"✅ Extracted shapefile to: {shp_path}")

            try:
                gdf = gpd.read_file(shp_path)
            except Exception as e:
                logger.error(f"Shapefile reading error: {e}")

            return gdf

    @property
    def alias_map(self) -> dict:
        return {
            field.alias: name
            for name, field in self.model.model_fields.items()
            if field.alias != name
        }

    def validate(
        self, gdf: gpd.GeoDataFrame, tolerance: float = 0.05, tag: str = "🔥"
    ) -> Tuple[gpd.GeoDataFrame, float]:
        # vocation to become a general method in a parent class
        validated_rows, validated_geoms = [], []
        n_skipped: int = 0

        for idx, row in gdf.iterrows():
            try:
                model_instance = self.model.model_validate(row.to_dict())
                validated_rows.append(model_instance.model_dump())
                validated_geoms.append(row["geometry"])
            except ValidationError as e:
                n_skipped += 1
                print(
                    f"⚠️ Validation error (row {idx}):\n{row.to_dict()}\n: {e.errors()[0]['msg']}"
                )

        if len(validated_rows) > 0:
            logger.success(
                f"{tag}\t✅ {len(validated_rows)} records passed validation."
            )
        if n_skipped > 0:
            logger.warning(
                f"{tag}\t⚠ {n_skipped} samples did not comform to expectations and were skipped."
            )

        pass_rate: float = len(validated_rows) / len(gdf)

        if pass_rate > (1 - tolerance):
            logger.success(f"{tag}\t🌏 Healthy data state ({pass_rate:.0%}) success.")
        else:
            logger.error(
                f"{tag}\t🚨 {pass_rate:.0%} of rows conformed to the FirePoint data model."
            )

        validated_gdf = gpd.GeoDataFrame(
            validated_rows, geometry=validated_geoms, crs=gdf.crs
        )

        return validated_gdf, pass_rate

    def load(self, force_reload: bool = False, validate: bool = True):
        if self.gdf is not None and not force_reload:
            return self.gdf

        gdf = self._download_and_extract()

        # Basic cleaning
        gdf = gdf.to_crs("EPSG:4326")

        if validate:
            gdf, _ = self.validate(gdf)

        gdf = gdf.rename(columns=str.lower)

        self.gdf = gdf

    @property
    def data(
        self,
    ) -> gpd.GeoDataFrame:
        return self.gdf


if __name__ == "__main__":

    fdl = FirePointDataLoader()
