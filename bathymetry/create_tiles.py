"""
Create depth tiles using Mapzen terrarium elevation encoding.

Note: this requires rasterio 1.1; there are errors with 1.2 that impact
the warped VRT processing (proj init errors?).

Build a VRT of the individual tiles first:
gdalbuildvrt -overwrite -resolution lowest depth.vrt *.tif


Resampled version for tiles at zooms <= 4 created by resampling to 1 arc minute resolution:
```
gdal_translate -r bilinear -outsize 25% 25% depth.vrt depth_1min_bilinear.tif
gdal_translate -r bilinear -outsize 25% 25% depth_1min_bilinear.tif depth_15min_bilinear.tif
```

Note: bilinear is used as cubic overshoots values of 0 and would need to be clamped.

"""


from io import BytesIO

import numpy as np
from PIL import Image

from pymbtiles import MBtiles
from pymbtiles.ops import extend
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


# ### Render global scale using lower resolution data (~45 sec)
# tif_to_mbtiles(
#     "data/depth/depth_15min_bilinear.tif",
#     "tiles/depth_cubic_0_1.mbtiles",
#     0,
#     1,
#     tile_size=512,
#     metadata={
#         "name": "global bathymetry",
#         "version": "1.0.0",
#         "attribution": "GEBCO Compilation Group (2020) GEBCO 2020 Grid",
#     },
#     tile_renderer=tile_renderer,
#     resampling="cubic",
# )

# ### Render mid zooms using medium resolution (~9 min)
# tif_to_mbtiles(
#     "data/depth/depth_1min_bilinear.tif",
#     "tiles/depth_cubic_2_3.mbtiles",
#     2,
#     3,
#     tile_size=512,
#     metadata={
#         "name": "global bathymetry",
#         "version": "1.0.0",
#         "attribution": "GEBCO Compilation Group (2020) GEBCO 2020 Grid",
#     },
#     tile_renderer=tile_renderer,
#     resampling="cubic",
# )


### Render higher zooms using higher resolution data (~3+ hours)
# NOTE: this is really only good until z6, then it starts getting crosshatching

# if using 2x rendering, can get to about z7 and it is OK

# tif_to_mbtiles(
#     "data/depth/depth.vrt",
#     "tiles/depth_cubic.mbtiles",
#     4,
#     8,
#     tile_size=512,
#     metadata={
#         "name": "global bathymetry",
#         "version": "1.0.0",
#         "attribution": "GEBCO Compilation Group (2020) GEBCO 2020 Grid",
#     },
#     tile_renderer=tile_renderer,
#     resampling="cubic",
# )

### Merge tilesets
# NOTE: this does not overwrite tiles in target if they already exist
# target_filename = "tiles/depth_cubic.mbtiles"
# extend("tiles/depth_cubic_2_3.mbtiles", target_filename)
# extend("tiles/depth_cubic_0_1.mbtiles", target_filename)

# with MBtiles(target_filename, "r+") as out:
#     out.meta["minzoom"] = 0


### Render blue earth data

tif_to_mbtiles(
    "data/depth/blue_earth/blue_earth.tif",
    "tiles/depth_blue_earth.mbtiles",
    0,
    8,
    tile_size=512,
    metadata={
        "name": "global bathymetry",
        "version": "1.0.0",
        "attribution": "GEBCO Compilation Group (2020) GEBCO 2020 Grid / Blue Earth Bathymetry (Tom Patterson, 2020)",
    },
    tile_renderer=tile_renderer,
    resampling="cubic",
)
