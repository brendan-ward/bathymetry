# Bathymetry Data Processing Pipeline

The goal of this project is to create depth polygons and elevation-encoded PNG tiles
for use in Mapbox GL basemaps.

## Data

GEBCO 2020 data were downloaded from: https://www.gebco.net/data_and_products/gridded_bathymetry_data/

GEBCO 2020 provides global coverage of elevation data on a 15 arc-second grid.

### Data Credits

GEBCO Compilation Group (2020) GEBCO 2020 Grid (doi:10.5285/a29c5465-b138-234d-e053-6c86abc040b9)

## Dependencies

This uses Python 3.8.

Packages:

-   `networkx`
-   `geopandas` (master)
-   `pygeos` (master)
-   `pygrio` (master)
-   `rasterio` (vectorized_shapes branch in my fork)
-   `raster-tilecutter`

## Preprocessing

Raster data were first clipped to depths <= 0, so that elevation polygons and grids
are not created for terrestrial areas.

GDAL VRTs were used to keep the existing individual datasets from GEBCO throughout;
merging the rasters into a single file makes for a very big file (>7 GB).

## Elevation encoding

This uses the Mapzen terrarium encoding in `create_tiles.py`.

Elevation tiles for zooms 0 - 10 take about 9.5 hours to create. Currently in Mapbox GL JS,
these only render correctly to about zoom 7.
