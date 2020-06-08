"""
Create depth tiles using Mapzen terrarium elevation encoding.

Note: this requires rasterio 1.1; there are errors with 1.2 that impact
the warped VRT processing (proj init errors?).

Build a VRT of the individual tiles first:
gdalbuildvrt -overwrite -resolution lowest depth.vrt *.tif
"""


from io import BytesIO

import numpy as np
from PIL import Image

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

    v = tile_data.flatten() + 32768

    # data are integers, no decimal component to include into blue,
    # so we leave that as 0
    rgb = np.zeros(shape=(v.shape[0], 3), dtype="uint8")
    rgb[:, 0] = np.floor(v / 256)
    rgb[:, 1] = np.floor(v % 256)

    img = Image.frombuffer("RGB", tile_data.shape[::-1], rgb, "raw", "RGB", 0, 1)

    buf = BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)  # rewind to beginning of buffer
    return buf.read()


tif_to_mbtiles(
    "data/depth/depth.vrt",
    "tiles/depth.mbtiles",
    0,
    10,
    tile_size=256,
    metadata={
        "name": "global bathymetry",
        "version": "1.0.0",
        "attribution": "GEBCO Compilation Group (2020) GEBCO 2020 Grid",
    },
    tile_renderer=tile_renderer,
)
