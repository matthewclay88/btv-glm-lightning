import json
import os
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

OUTPUT_DIR = "data"
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "lightning.json")

# goes2go downloads here on GitHub Actions
GOES_DOWNLOAD_ROOT = os.path.expanduser("~/data")

# ==========================================================
# FUNCTIONS
# ==========================================================

def load_btv_polygon():
    print("Loading BTV CWA...")

    gdf = gpd.read_file(GEOJSON_URL)
    btv = gdf[gdf["CWA"] == "BTV"]

    print(f"Loaded {len(btv)} forecast zones.")

    return btv.union_all()


def get_glm_files():
    print("Finding last hour of GLM data...")

    G = GOES(
        satellite=19,
        product="GLM-L2-LCFA"
    )

    files = G.timerange(recent=timedelta(hours=1))

    print(f"Found {len(files)} files.")

    return files


def process_files(files, polygon):

    now = datetime.now(timezone.utc)

    counts = {
        "5": 0,
        "15": 0,
        "30": 0,
        "60": 0
    }

    processed = 0

    for _, row in files.iterrows():

        try:

            local_file = os.path.join(
                GOES_DOWNLOAD_ROOT,
                row.file
            )

            if not os.path.exists(local_file):
                print(f"Missing: {local_file}")
                continue

            ds = xr.load_dataset(local_file)

            lats = ds.flash_lat.values
            lons = ds.flash_lon.values

            times = pd.to_datetime(
                ds.flash_time_offset_of_first_event.values,
                utc=True
            )

            for lat, lon, flash_time in zip(lats, lons, times):

                pt = Point(float(lon), float(lat))

                if not polygon.covers(pt):
                    continue

                age = (
                    now - flash_time.to_pydatetime()
                ).total_seconds() / 60

                if age <= 60:
                    counts["60"] += 1

                if age <= 30:
                    counts["30"] += 1

                if age <= 15:
                    counts["15"] += 1

                if age <= 5:
                    counts["5"] += 1

            processed += 1

            ds.close()

        except Exception as e:

            print()
            print("=" * 60)
            print("FAILED")
            print(local_file)
            print(e)
            print("=" * 60)
            print()

    return processed, counts


def write_json(processed, counts):

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "processed_files": processed,
        "counts": counts
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2)

    print()
    print("=" * 60)
    print("Lightning Processing Complete")
    print("=" * 60)
    print(json.dumps(output, indent=2))


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    polygon = load_btv_polygon()

    files = get_glm_files()

    processed, counts = process_files(
        files,
        polygon
    )

    write_json(
        processed,
        counts
    )
