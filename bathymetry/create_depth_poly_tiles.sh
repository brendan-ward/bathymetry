#!/bin/bash

# Create tiles of depth polygons using tippecanoe
# Input are preprocessed using create_blue_earth_polygons.py


TMPDIR="/tmp"
TILEDIR="tiles"
SRCDIR="data/poly/blue_earth"

echo "Creating lowest resolution tiles..."
ogr2ogr -f GeoJSONSeq $TMPDIR/depth_8x.json $SRCDIR/blue_earth_8x.fgb blue_earth_8x -lco COORDINATE_PRECISION=3 -progress
tippecanoe -f -pg -Z 0 -z 1 -P --drop-smallest-as-needed  --detect-shared-borders --simplification=4 -o $TMPDIR/depth_8x.mbtiles -l "depth" $TMPDIR/depth_8x.json


echo "Creating low resolution tiles..."
ogr2ogr -f GeoJSONSeq $TMPDIR/depth_4x.json $SRCDIR/blue_earth_4x.fgb blue_earth_4x -lco COORDINATE_PRECISION=3 -progress
tippecanoe -f -pg -Z 2 -z 3 -P --drop-smallest-as-needed  --detect-shared-borders --simplification=4 -o $TMPDIR/depth_4x.mbtiles -l "depth" $TMPDIR/depth_4x.json

echo "Creating moderate resolution tiles..."
ogr2ogr -f GeoJSONSeq $TMPDIR/depth_2x.json $SRCDIR/blue_earth_2x.fgb blue_earth_2x -lco COORDINATE_PRECISION=4 -progress
tippecanoe -f -pg -Z 4 -z 5 -P --drop-smallest-as-needed  --detect-shared-borders --simplification=3 -o $TMPDIR/depth_2x.mbtiles -l "depth" $TMPDIR/depth_2x.json

echo "Creating higher resolution tiles..."
ogr2ogr -f GeoJSONSeq $TMPDIR/depth.json $SRCDIR/blue_earth.fgb blue_earth -lco COORDINATE_PRECISION=5 -progress
tippecanoe -f -pg -Z 6 -z 8 -P --drop-smallest-as-needed  --detect-shared-borders --simplification=2 -o $TMPDIR/depth.mbtiles -l "depth" $TMPDIR/depth.json


# merge together
echo "Merging tilesets..."
tile-join -f -pg -o $TILEDIR/depth_contours.mbtiles $TMPDIR/depth_8x.mbtiles $TMPDIR/depth_4x.mbtiles $TMPDIR/depth_2x.mbtiles $TMPDIR/depth.mbtiles
