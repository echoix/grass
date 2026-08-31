#!/usr/bin/env bash

# The make step requires something like:
# export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$PREFIX/lib"
# further steps additionally require:
# export PATH="$PATH:$PREFIX/bin"

# fail on non-zero return code from a subprocess
set -e

# print commands
set -x

if [ -z "$1" ]; then
    echo "Usage: $0 PREFIX"
    exit 1
fi

# Adding -Werror to make's CFLAGS is a workaround for configuring with
# an old version of configure, which issues compiler warnings and
# errors out. This may be removed with upgraded configure.in file.
makecmd="make"
if [[ "$#" -ge 2 ]]; then
    ARGS=("$@")
    makecmd="make CFLAGS='$CFLAGS ${ARGS[@]:1}' CXXFLAGS='$CXXFLAGS ${ARGS[@]:1}'"
fi

# non-existent variables as an errors
set -u

export INSTALL_PREFIX=$1

# Extra configure args added under coverage; keep declared under `set -u`.
OPENMP_ARGS=()

# LLVM source-based coverage instrumentation, opt-in via env var. Requires
# clang (installed via apt.txt). Kept out of the default O2 path so
# non-coverage runs are unaffected.
if [ "${GRASS_LLVM_COVERAGE:-0}" = "1" ]; then
    export CC="${CC:-clang}"
    export CXX="${CXX:-clang++}"
    # LLVM source-based coverage generates its region mapping before the
    # optimizer runs, so optimization does not affect coverage quality
    # (clang doc: SourceBasedCodeCoverage, "Impact of llvm optimizations
    # on coverage reports"). Keep the project's normal -O2 to hold the
    # runtime impact small. -fprofile-update=atomic makes counter
    # increments atomic; required for GRASS's OpenMP-parallel regions
    # (e.g. r.univar) so threads racing on shared counters do not lose
    # updates.
    #
    # Setting CFLAGS explicitly at configure time suppresses autoconf's
    # default "-g -O2", so pass -O2 here.
    COV_FLAGS="-fprofile-instr-generate -fcoverage-mapping -fprofile-update=atomic"
    export CFLAGS="${CFLAGS:--O2} ${COV_FLAGS}"
    export CXXFLAGS="${CXXFLAGS:--O2} ${COV_FLAGS}"
    export LDFLAGS="${LDFLAGS:-} -fprofile-instr-generate -fcoverage-mapping"
    # Clang ships omp.h in its resource-dir instead of /usr/include, so
    # configure's plain omp.h check misses it. Point configure at both
    # the include and (from apt libomp-dev) the runtime lib.
    CLANG_RES_DIR="$("${CC}" -print-resource-dir 2>/dev/null || true)"
    if [ -n "${CLANG_RES_DIR}" ] && [ -d "${CLANG_RES_DIR}/include" ]; then
        OPENMP_ARGS+=("--with-openmp-includes=${CLANG_RES_DIR}/include")
    fi
fi

./configure \
    --enable-largefile \
    --prefix="$INSTALL_PREFIX/" \
    --with-blas \
    --with-bzlib \
    --with-cxx \
    --with-fftw \
    --with-freetype \
    --with-freetype-includes="/usr/include/freetype2/" \
    --with-geos \
    --with-lapack \
    --with-libsvm \
    --with-netcdf \
    --with-openmp \
    --with-pdal \
    --with-proj-share=/usr/share/proj \
    --with-pthread \
    --with-readline \
    --with-sqlite \
    --with-tiff \
    --with-zstd \
    ${OPENMP_ARGS[@]+"${OPENMP_ARGS[@]}"}

eval $makecmd
make install
