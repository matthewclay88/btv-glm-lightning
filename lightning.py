from goes2go import GOES

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
