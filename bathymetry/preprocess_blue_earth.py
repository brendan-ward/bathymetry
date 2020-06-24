"""
Preprocess Blue Earth Bathymetry data.
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
src = rasterio.open(data_dir / "source/blue_earth/Blue-Earth-Bathymetry.tif")
data = src.read(1)

# zero out everything >= 0
data[data > 0] = 0

meta = src.meta.copy()
meta.update({"driver": "GTIFF"})
with rasterio.open(data_dir / "depth/blue_earth/blue_earth.tif", "w", **meta) as out:
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

with rasterio.open(data_dir / "binned/blue_earth/blue_earth.tif", "w", **meta) as out:
    out.write_band(1, data)

