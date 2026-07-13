from goes2go import GOES

print("Connecting to GOES...")

G = GOES(
    satellite=19,
    product="GLM-L2-LCFA"
)

print("GOES object created successfully!")

print("Downloading latest GLM file...")

ds = G.latest()

print(ds)
