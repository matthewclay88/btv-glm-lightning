import json
from datetime import datetime, timedelta, timezone

import geopandas as gpd
import pandas as pd
import xarray as xr
from shapely.geometry import Point

from goes2go import GOES


# ==========================================================
# CONFIGURATION
# ==========================================================

GEOJSON_URL = (
    "https://raw.githubusercontent.com/"
    "matthewclay88/severe-climatology/main/allzones.geojson"
)

OUTPUT_JSON = "data/lightning.json"


# ==========================================================
# LOAD BTV CWA
# ==========================================================

print("Loading BTV CWA...")

cwa = gpd.read_file(GEOJSON_URL)
btv = cwa[cwa["CWA"] == "BTV"]
btv_polygon = btv.union_all()

print(f"Loaded {len(btv)} BTV forecast zones.")


# ==========================================================
# FIND LAST HOUR OF GLM FILES
# ==========================================================

print("Finding last hour of GLM data...")

G = GOES(
    satellite=19,
    product="GLM-L2-LCFA"
)

files = G.timerange(
    recent=timedelta(hours=1)
)

print(f"Found {len(files)} GLM files.")
print(files.columns)
print()
print(files.iloc[0])


# ==========================================================
# COUNT FLASHES
# ==========================================================

now = datetime.now(timezone.utc)

counts = {
    "5": 0,
    "15": 0,
    "30": 0,
    "60": 0
}

processed_files = 0

for _, row in files.iterrows():

    try:

        ds = xr.load_dataset(row.file)

        lats = ds.flash_lat.values
        lons = ds.flash_lon.values
        times = pd.to_datetime(
            ds.flash_time_offset_of_first_event.values,
            utc=True
        )

        for lat, lon, flash_time in zip(lats, lons, times):

            point = Point(float(lon), float(lat))

            if not btv_polygon.contains(point):
                continue

            age_minutes = (now - flash_time.to_pydatetime()).total_seconds() / 60.0

            if age_minutes <= 60:
                counts["60"] += 1

            if age_minutes <= 30:
                counts["30"] += 1

            if age_minutes <= 15:
                counts["15"] += 1

            if age_minutes <= 5:
                counts["5"] += 1

        processed_files += 1

    except Exception as e:

        print("================================")
        print("FAILED FILE")
        print(row)
        print(e)
        print("================================")
# ==========================================================
# WRITE JSON
# ==========================================================

output = {
    "updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "processed_files": processed_files,
    "counts": counts
}

with open(OUTPUT_JSON, "w") as f:
    json.dump(output, f, indent=2)

print()
print("===================================")
print("Lightning processing complete")
print("===================================")
print(json.dumps(output, indent=2))
