"""
Read GEBCO 2020 data and preprocess depth for later analyses.

First, build a VRT in the source directory:
gdalbuildvrt -overwrite -resolution lowest gebco2020.vrt *.tif
"""

from pathlib import Path
from time import time

import numpy as np
import rasterio
from rasterio.features import sieve

from bathymetry.constants import BINS

# minimum number of pixels per polygon
MIN_PIXELS = 100


data_dir = Path("data")


### Read in each source, and crop it to <= 0 depth
for filename in (data_dir / "source").glob("*.tif"):
    print(f"Processing {filename}")
    src = rasterio.open(filename)
    data = src.read(1)

    # zero out everything >= 0
    data[data > 0] = 0

    meta = src.meta.copy()
    # "nodata": 0,
    # NOTE: we keep 0's as valid so they don't break the mapbox elevation decoder
    meta.update({"driver": "GTIFF"})
    with rasterio.open(data_dir / "depth" / filename.name, "w", **meta) as out:
        out.write_band(1, data)

    # convert everthing from elevation (negative) to depth (positive)
    data = np.abs(data)

    # bin depths
    nonzero_ix = data != 0
    data[nonzero_ix] = np.digitize(data[nonzero_ix], BINS)
    data = data.astype("uint8")

    # sieve out any areas < min_poly_pixels
    sieved = sieve(data, size=MIN_PIXELS)

    # stamp back in the areas of 0 (could be islands) even if small
    data = np.where(data == 0, 0, sieved)

    meta = src.meta.copy()
    meta.update({"dtype": "uint8", "nodata": 0})

    with rasterio.open(data_dir / "binned" / filename.name, "w", **meta) as out:
        out.write_band(1, data)


### Version to read from VRT and merge into single file (>7 GB).

# src = rasterio.open(src_dir / "gebco2020.vrt")
# data = src.read(1)

# # zero out everything >= 0
# data[data > 0] = 0

# meta = src.meta.copy()
# meta.update({"nodata": 0, "driver": "GTIFF"})
# with rasterio.open(out_dir / "depth.tif", "w", **meta) as out:
#     out.write_band(1, data)
