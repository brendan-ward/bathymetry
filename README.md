# Bathymetry Data Processing Pipeline

The goal of this project is to create depth polygons and elevation-encoded PNG tiles
for use in Mapbox GL basemaps.

## Data

GEBCO 2020 data were downloaded from: https://www.gebco.net/data_and_products/gridded_bathymetry_data/

GEBCO 2020 provides global coverage of elevation data on a 15 arc-second grid.

Blue Earth Bathymetry data were downloaded from: http://www.shadedrelief.com/blue-earth/
on 6/23/2020.

### Data Credits

GEBCO Compilation Group (2020) GEBCO 2020 Grid (doi:10.5285/a29c5465-b138-234d-e053-6c86abc040b9)

Blue Earth Bathymetry data were processed by Tom Patterson.

## Preprocessing

Raster data were first clipped to depths <= 0, so that elevation polygons and grids
are not created for terrestrial areas.

GDAL VRTs were used to keep the existing individual datasets from GEBCO throughout;
merging the rasters into a single file makes for a very big file (>7 GB).

Blue Earth Bathymetry data were preprocessed using `bathymetry/preprocess_blue_earth.py`.

## Elevation encoding

This uses the Mapzen terrarium encoding in `create_tiles.py`.

Elevation tiles for zooms 0 - 10 take about 9.5 hours to create. Currently in Mapbox GL JS,
these only render correctly to about zoom 7. There appears to be linear chatter in
the derived elevation output; we don't know yet if this comes from the underlying
GEBCO data or the WarpedVRT resampling used to create the tiles.

TODO: this might come from using cubic; bilinear may be a better option according to https://tilemill-project.github.io/tilemill/docs/guides/terrain-data/

## Hillshade to polygons

EXPERIMENTAL:
Convert blue earth depth data to hillshade (recommendation of z value comes from: http://www.shadedrelief.com/blue-earth/).

TODO: project to 3857 first, then adjust scale (`-s`) to balance out level of detail.
Using scale of 1000 highlights the steepest gradients, and thresholded at 175 does a reasonable job of accenting major features without too much noise. (fine detail can then be dropped from this). Also scale at 100 and thresholded at 50,100 also does a nice job of level of detail.

```bash
gdaldem hillshade -az 335 blue_earth.tif -z 1000 -s 100 blue_earth_hillshade.tif
```

Thresholding this at approx 50, 100, 150 seems to separate out sides of a slope reasonably well.

See also: https://gis.stackexchange.com/questions/144535/creating-transparent-hillshade
