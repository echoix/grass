#!/usr/bin/env bash

# fail on non-zero return code from a subprocess
set -e

if [[ -z "${PYTHON}" ]]; then
  PYTHON="python3"
else
  PYTHON="${PYTHON}"
fi

grass --tmp-project XY --exec \
    g.download.project url=https://grass.osgeo.org/sampledata/north_carolina/nc_spm_full_v2alpha2.tar.gz path=$HOME

grass --tmp-project XY --exec \
    ${PYTHON} -m grass.gunittest.main \
    --grassdata $HOME --location nc_spm_full_v2alpha2 --location-type nc \
    --min-success 100 $@
