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

print()

print("Available GOES methods:")

print(dir(G))
