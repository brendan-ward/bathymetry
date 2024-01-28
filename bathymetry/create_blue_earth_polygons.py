from pathlib import Path
from time import time

import numpy as np
import pandas as pd
import rasterio
from rasterio import Affine as A
from rasterio.features import shapes
import geopandas as gp
from pyogrio.geopandas import write_dataframe
import shapely

from bathymetry.constants import BINS


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

    # set mask=(data != 0).astype("bool")
    # to exclude 0 as nodata instead of leaving in as polygons

    features = list(shapes(data, transform=transform))

    values = np.zeros(
        shape=(
            len(
                features,
            )
        ),
        dtype="uint8",
    )
    polygons = np.empty(shape=(len(features)), dtype="object")
    for i, (feature, value) in enumerate(features):
        exterior = feature["coordinates"][0]
        interiors = feature["coordinates"][1:]
        if interiors:
            geom = shapely.polygons(
                exterior, [shapely.linearrings(r) for r in interiors]
            )
        else:
            geom = shapely.polygons(exterior)

        values[i] = value
        polygons[i] = geom

    return gp.GeoDataFrame({"geometry": polygons, "bin": values}, crs="EPSG:4326")


def create_polygons_chunked(data):
    """Divide the data up into quadrants, create polygons from each, then merge

    Parameters
    ----------
    data : ndarray
    """
    y_split = data.shape[0] // 2
    x_split = data.shape[1] // 2

    # -180:0,90:0
    chunk = data[:y_split, :x_split]
    df = create_polygons(chunk, src.transform)
    merged = df

    # 0:180,90:0
    chunk = data[:y_split, x_split:]
    df = create_polygons(chunk, src.transform * A.translation(x_split, 0))
    merged = pd.concat([merged, df], ignore_index=True)

    # -180:0,0:-90
    chunk = data[y_split:, :x_split]
    df = create_polygons(chunk, src.transform * A.translation(0, y_split))
    merged = pd.concat([merged, df], ignore_index=True)

    # 0:180,0:-90
    chunk = data[y_split:, x_split:]
    df = create_polygons(chunk, src.transform * A.translation(x_split, y_split))
    merged = pd.concat([merged, df], ignore_index=True)

    return merged


src_dir = Path("data/binned/blue_earth")
out_dir = Path("data/poly/blue_earth")
out_dir.mkdir(exist_ok=True, parents=True)


inputs = [
    "blue_earth_8x.tif",
    "blue_earth_4x.tif",
    "blue_earth_2x.tif",
    "blue_earth.tif",
]

for filename in inputs:
    print("Processing", filename)
    src = rasterio.open(src_dir / filename)
    data = src.read(1)

    start = time()

    # No need to chunk for Blue Earth but do need to chunk for GEBCO
    # df = create_polygons_chunked(data)

    df = create_polygons(data, src.transform)

    df["depth"] = df.bin.map({i: v for i, v in enumerate(BINS)}).astype("uint16")

    print(f"{len(df)} polygons created in {time() - start:.2f}s")

    outfilename = filename.replace(".tif", ".fgb")
    write_dataframe(df, str(out_dir / outfilename))
