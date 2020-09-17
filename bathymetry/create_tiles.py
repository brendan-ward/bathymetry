"""
Create depth tiles using Mapzen terrarium elevation encoding.

Note: this requires rasterio 1.1; there are errors with 1.2 that impact
the warped VRT processing (proj init errors?).


Note: bilinear is used as cubic overshoots values of 0 and would need to be clamped.
"""

from time import time
from pathlib import Path
from io import BytesIO

import numpy as np
from PIL import Image

from pymbtiles import MBtiles
from pymbtiles.ops import extend, union
from tilecutter.mbtiles import tif_to_mbtiles


def tile_renderer(tile_data):
    """Use Mapzen terrarium elevation encoding to encode
    integer depth data to RGB (24bit) PNG bytes.

    Parameters
    ----------
    tile_data : 2D int16
        depth data within tile

    Returns
    -------
    bytes
        RGB PNG bytes
    """

    if tile_data.min() == 0:
        # tile is only covered by land
        return None

    v = (tile_data.flatten() + 32768).astype("float32")

    rgb = np.zeros(shape=(v.shape[0], 3), dtype="uint8")
    rgb[:, 0] = np.floor(v / 256.0)
    rgb[:, 1] = np.floor(v % 256)
    rgb[:, 2] = np.floor((v * 256.0) % 256)

    # TODO: if there are few pixel values, encode as paletted PNG instead
    img = Image.frombuffer("RGB", tile_data.shape[::-1], rgb, "raw", "RGB", 0, 1)

    buf = BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)  # rewind to beginning of buffer
    return buf.read()


### Render blue earth data

# create batches by zoom level, merge back later
# zones 9-10 takes 9.35 hours
# zone 10 appears to be beyond useful resolution for these data
# batches = [[0, 8], [9, 10]]


# batch = batches[1]


# min_zoom, max_zoom = batch
# outfilename = tmp_dir / f"depth_blue_earth_{min_zoom}_{max_zoom}.mbtiles"
# tif_to_mbtiles(
#     src,
#     outfilename,
#     min_zoom=min_zoom,
#     max_zoom=max_zoom,
#     tile_size=512,
#     metadata={
#         "name": "global bathymetry",
#         "version": "1.0.0",
#         "attribution": "GEBCO Compilation Group (2020) GEBCO 2020 Grid / Blue Earth Bathymetry (Tom Patterson, 2020)",
#     },
#     tile_renderer=tile_renderer,
#     resampling="bilinear",
# )


# print("Merging tilesets...")
# start = time()
# tileset_filename = "tiles/depth_blue_earth.mbtiles"

# filenames = [
#     tmp_dir / f"depth_blue_earth_{min_zoom}_{max_zoom}.mbtiles"
#     for min_zoom, max_zoom in batches
# ]
# # flip the order so we merge into the bigger ones
# filenames.reverse()

# # union the first 2
# union(filenames[0], filenames[1], tileset_filename)

# # extend in the rest
# for filename in filenames[2:]:
#     extend(filename, tileset_filename)

# # update the metadata
# with MBtiles(tileset_filename, "r+") as tileset:
#     tileset.meta["minzoom"] = batches[0][0]
#     tileset.meta["maxzoom"] = batches[-1][-1]


### Previous runs
# tif_to_mbtiles(
#     "data/depth/blue_earth/blue_earth.tif",
#     "tiles/depth_blue_earth.mbtiles",
#     0,
#     8,
#     tile_size=512,
#     metadata={
#         "name": "global bathymetry",
#         "version": "1.0.0",
#         "attribution": "GEBCO Compilation Group (2020) GEBCO 2020 Grid / Blue Earth Bathymetry (Tom Patterson, 2020)",
#     },
#     tile_renderer=tile_renderer,
#     resampling="cubic",
# )
