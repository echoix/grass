#!/usr/bin/env bash
# Author: Ivan Mincik, ivan.mincik@gmail.com

set -e
set -x
dpkg -l
dpkg -l --selected-only
sudo apt-get update -y
    sudo apt-get install -y wget git gawk findutils pkg-config libpdal-plugins
    xargs -a <(awk '! /^ *(#|$)/' ".github/workflows/apt.txt") -r -- \
        sudo apt-get install -y --no-install-recommends --no-install-suggests

# https://github.com/qgis/QGIS/issues/56285
dpkg -l | grep pdal
apt rdepends libpdal-util13
apt depends libpdal-base13
apt depends libpdal16
apt depends libpdal-dev
apt policy libpdal-dev
apt policy pdal
dpkg -l
dpkg -l --selected-only
