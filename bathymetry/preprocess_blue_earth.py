"""
Preprocess Blue Earth Bathymetry data.
"""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import sieve
from rasterio.warp import reproject, Resampling

from bathymetry.constants import BINS

# minimum number of pixels per polygon
MIN_PIXELS = 100

data_dir = Path("data")
src_dir = data_dir / "source/blue_earth"
depth_dir = data_dir / "depth/blue_earth"
depth_dir.mkdir(exist_ok=True, parents=True)
binned_dir = data_dir / "binned/blue_earth"
binned_dir.mkdir(exist_ok=True, parents=True)


### Read in each source, and crop it to <= 0 depth
src = rasterio.open(src_dir / "Blue-Earth-Bathymetry.tif")
data = src.read(1)

# zero out everything >= 0
data[data > 0] = 0

meta = src.meta.copy()
meta.update({"driver": "GTIFF"})
with rasterio.open(depth_dir / "blue_earth.tif", "w", **meta) as out:
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
meta.update({"dtype": "uint8", "nodata": 255})

with rasterio.open(binned_dir / "blue_earth.tif", "w", **meta) as out:
    out.write_band(1, data)


### 2x: Resample and sieve to coarser resolution
scale_factor = 2
scaled = np.zeros(
    shape=(src.width // scale_factor, src.height // scale_factor), dtype=data.dtype
)
_, transform = reproject(
    data,
    scaled,
    src_transform=src.transform,
    src_crs=src.crs,
    dst_crs=src.crs,
    resampling=Resampling.nearest,
)

# sieve out fine detail
scaled = sieve(scaled, size=10)

scaled_meta = meta.copy()
scaled_meta.update(
    {"width": scaled.shape[1], "height": scaled.shape[0], "transform": transform}
)

with rasterio.open(binned_dir / "blue_earth_2x.tif", "w", **scaled_meta) as out:
    out.write_band(1, scaled)

### 4x: Resample and sieve to coarser resolution
scale_factor = 2
scaled_height, scaled_width = scaled.shape
scaled_4x = np.zeros(
    shape=(scaled_width // scale_factor, scaled_height // scale_factor),
    dtype=data.dtype,
)
_, transform = reproject(
    scaled,
    scaled_4x,
    src_transform=transform,
    src_crs=src.crs,
    dst_crs=src.crs,
    resampling=Resampling.nearest,
)

# sieve out fine detail
scaled_4x = sieve(scaled_4x, size=100)

scaled_meta = meta.copy()
scaled_meta.update(
    {"width": scaled_4x.shape[1], "height": scaled_4x.shape[0], "transform": transform}
)

with rasterio.open(binned_dir / "blue_earth_4x.tif", "w", **scaled_meta) as out:
    out.write_band(1, scaled_4x)


### 8x: Resample and sieve to coarser resolution
scale_factor = 4
scaled_height, scaled_width = scaled_4x.shape
scaled_8x = np.zeros(
    shape=(scaled_width // scale_factor, scaled_height // scale_factor),
    dtype=data.dtype,
)
_, transform = reproject(
    scaled_4x,
    scaled_8x,
    src_transform=transform,
    src_crs=src.crs,
    dst_crs=src.crs,
    resampling=Resampling.nearest,
)

# sieve out fine detail
scaled_8x = sieve(scaled_8x, size=10)

scaled_meta = meta.copy()
scaled_meta.update(
    {"width": scaled_8x.shape[1], "height": scaled_8x.shape[0], "transform": transform}
)

with rasterio.open(binned_dir / "blue_earth_8x.tif", "w", **scaled_meta) as out:
    out.write_band(1, scaled_8x)
