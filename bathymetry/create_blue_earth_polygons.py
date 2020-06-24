from pathlib import Path
from time import time

import numpy as np
import rasterio
from rasterio import Affine as A
from rasterio.warp import reproject, Resampling
from rasterio.features import sieve, shapes
import geopandas as gp
import pygeos as pg
from pyogrio.geopandas import write_dataframe

from bathymetry.constants import BINS


# SCALE_FACTOR = 8
# minimum number of pixels per polygon
MIN_PIXELS = 1000


def create_polygons(data, transform):
    """Create polygons from data based on spatial coordinates specified by
    transform.

    Parameters
    ----------
    data : 2D array
        values to convert to polygons
    transform : rasterio transform object

    Returns
    -------
    GeoDataFrame
        contains geometry and values
    """
    # NOTE: Scale the transform to match the smaller cell size
    features = list(shapes(data, mask=(data != 0).astype("bool"), transform=transform))

    values = np.zeros(shape=(len(features,)), dtype="uint8")
    polygons = np.empty(shape=(len(features)), dtype="object")
    for i, (feature, value) in enumerate(features):
        exterior = feature["coordinates"][0]
        interiors = feature["coordinates"][1:]
        if interiors:
            geom = pg.polygons(exterior, [pg.linearrings(r) for r in interiors])
        else:
            geom = pg.polygons(exterior)

        values[i] = value
        polygons[i] = geom

    return gp.GeoDataFrame({"geometry": polygons, "bin": values}, crs="EPSG:4326")


src_dir = Path("data/binned/blue_earth")
out_dir = Path("data/poly/blue_earth")


# TODO: can use the VRT and convert polygons in smaller chunks
# just need to set transform correctly

src = rasterio.open(src_dir / "blue_earth.tif")
data = src.read(1)

start = time()

y_split = data.shape[0] // 2
x_split = data.shape[1] // 2

# -180:0,90:0
chunk = data[:y_split, :x_split]
df = create_polygons(chunk, src.transform)
merged = df

# 0:180,90:0
chunk = data[:y_split, x_split:]
df = create_polygons(chunk, src.transform * A.translation(x_split, 0))
merged = merged.append(df)

# -180:0,0:-90
chunk = data[y_split:, :x_split]
df = create_polygons(chunk, src.transform * A.translation(0, y_split))
merged = merged.append(df)

# 0:180,0:-90
chunk = data[y_split:, x_split:]
df = create_polygons(chunk, src.transform * A.translation(x_split, y_split))
merged = merged.append(df)

df = merged
print(f"{len(df)} polygons created in {time() - start:.2f}s")

df["depth"] = df.bin.map({i: v for i, v in enumerate(BINS)}).astype("uint16")


write_dataframe(df, str(out_dir / "blue_earth.shp"))

# TODO: write polygons for tippecanoe map tiles
write_dataframe(df, "/tmp/blue_earth.json", driver="GeoJSONSeq")


# create tiles
# tippecanoe -f -pg -Z 0 -z 8 -P --drop-smallest-as-needed  --detect-shared-borders --simplification=4 -o tiles/depth_contours_blue_earth.mbtiles -l "depth" /tmp/blue_earth.json
