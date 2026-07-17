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
OUTPUT_GEOJSON = os.path.join(OUTPUT_DIR, "lightning.geojson")

GOES_DOWNLOAD_ROOT = os.path.expanduser("~/data")


# ==========================================================
# LOAD BTV CWA
# ==========================================================

def load_btv_polygon():

    print("Loading BTV CWA...")

    gdf = gpd.read_file(GEOJSON_URL)

    btv = gdf[gdf["CWA"] == "BTV"]

    print(f"Loaded {len(btv)} forecast zones.")

    return btv.union_all()


# ==========================================================
# FIND GLM FILES
# ==========================================================

def get_glm_files():

    print("Finding last hour of GLM data...")

    G = GOES(
        satellite=19,
        product="GLM-L2-LCFA"
    )

    try:
        files = G.timerange(
            recent=timedelta(hours=2)   # wider window absorbs upload latency
        )
    except ValueError as e:
        print(f"No GLM files available yet ({e}); skipping this run.")
        files = pd.DataFrame(columns=["file"])  # empty, downstream code handles it fine

    print(f"Found {len(files)} files.")

    return files


# ==========================================================
# PROCESS FILES
# ==========================================================

def process_files(files, polygon):

    now = datetime.now(timezone.utc)

    counts = {
        "5": 0,
        "15": 0,
        "30": 0,
        "60": 0
    }

    features = []

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

                # --------------------------------------
                # Save GeoJSON point (last 60 minutes)
                # --------------------------------------

                if age <= 60:

                    if age <= 5:
                        bin_name = "0-5"
                    elif age <= 15:
                        bin_name = "5-15"
                    elif age <= 30:
                        bin_name = "15-30"
                    else:
                        bin_name = "30-60"

                    features.append({

                        "type": "Feature",

                        "geometry": {
                            "type": "Point",
                            "coordinates": [
                                float(lon),
                                float(lat)
                            ]
                        },

                        "properties": {

                            "time": flash_time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ"
                            ),

                            "age_minutes": round(age, 1),

                            "minutes_bin": bin_name

                        }

                    })

                # --------------------------------------
                # Counts
                # --------------------------------------

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

    return processed, counts, features


# ==========================================================
# WRITE KPI JSON
# ==========================================================

def write_json(processed, counts):

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output = {

        "updated":
            datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),

        "processed_files":
            processed,

        "counts":
            counts

    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2)

    print()
    print("=" * 60)
    print("Lightning JSON Written")
    print("=" * 60)
    print(json.dumps(output, indent=2))


# ==========================================================
# WRITE GEOJSON
# ==========================================================

def write_geojson(features):

    geojson = {

        "type": "FeatureCollection",

        "features": features

    }

    with open(OUTPUT_GEOJSON, "w") as f:
        json.dump(geojson, f, indent=2)

    print()
    print("=" * 60)
    print(f"GeoJSON Written ({len(features)} flashes)")
    print("=" * 60)


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    polygon = load_btv_polygon()

    files = get_glm_files()

    processed, counts, features = process_files(
        files,
        polygon
    )

    write_json(
        processed,
        counts
    )

    write_geojson(
        features
    )
