import geopandas as gpd
from goes2go import GOES
import goes2go
from shapely.geometry import Point
from datetime import timedelta

print("Connecting to GOES...")

G = GOES(
    satellite=19,
    product="GLM-L2-LCFA"
)

print("GOES object created successfully!")

print()

print("Downloading last hour of GLM data...")

datasets = G.timerange(recent=timedelta(hours=1))

print(type(datasets))
print(datasets)
