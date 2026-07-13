import geopandas as gpd
from goes2go import GOES
import goes2go
from shapely.geometry import Point

print("Connecting to GOES...")

G = GOES(
    satellite=19,
    product="GLM-L2-LCFA"
)

print("GOES object created successfully!")

print("Downloading latest GLM file...")

ds = G.latest()

print("Number of flashes:", len(ds.flash_lat))

print()
print("Flash Latitudes:")
print(ds.flash_lat.values[:10])

print()
print("Flash Longitudes:")
print(ds.flash_lon.values[:10])

print()
print("Flash Times:")
print(ds.flash_time_offset_of_first_event.values[:10])

print()

print("Loading BTV CWA...")

cwa = gpd.read_file(
    "https://raw.githubusercontent.com/matthewclay88/severe-climatology/main/allzones.geojson"
)

print("Columns:")
print(cwa.columns)

print()
print()

print("CWAs in file:")

# Keep only the BTV CWA polygons
btv = cwa[cwa["CWA"] == "BTV"]

print("Number of BTV forecast zones:", len(btv))

print()

print("Merging BTV forecast zones...")

btv_polygon = btv.union_all()

print("Done!")

print(f"Geometry type: {btv_polygon.geom_type}")
print(f"Bounds: {btv_polygon.bounds}")

print()
print("Testing Burlington...")

burlington = Point(-73.2121, 44.4759)

print("Burlington inside BTV:",
      btv_polygon.contains(burlington))

print()
print("Testing flashes inside BTV CWA...")

count = 0

for lat, lon in zip(ds.flash_lat.values, ds.flash_lon.values):

    point = Point(float(lon), float(lat))

    if btv_polygon.contains(point):
        count += 1

print(f"Flashes inside BTV: {count}")
