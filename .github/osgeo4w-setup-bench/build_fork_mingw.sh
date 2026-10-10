#!/bin/bash
# Builds the OSGeo4W setup of the fork (jef-n/OSGeo4W, src/setup) with the same
# mingw-w64 cross toolchain as build_upstream.sh instead of MSVC, to separate
# compiler effects from code effects.  bzip2 and zlib are compiled in from their
# sources, as in the MSVC build.  Runs in a Cygwin shell.
#
# usage: build_fork_mingw.sh <OSGeo4W checkout> <work dir> <output exe> <patch>...
set -euo pipefail
export PATH=/usr/bin:/usr/local/bin:/bin
git config --global --add safe.directory "*"

osgeo4w=$1
work=$2
out=$3
shift 3

ZLIB=1.3.2
BZIP2=1.0.8
mkdir -p "$work"
cd "$work"
[ -d zlib-$ZLIB ] || { curl -fsSL -o zlib.tar.gz https://github.com/madler/zlib/releases/download/v$ZLIB/zlib-$ZLIB.tar.gz && tar xzf zlib.tar.gz; }
[ -d bzip2-$BZIP2 ] || { curl -fsSL -o bzip2.tar.gz https://sourceware.org/pub/bzip2/bzip2-$BZIP2.tar.gz && tar xzf bzip2.tar.gz; }

# patch a copy of the sources, so that the checkout stays as it is
rm -rf fork
mkdir -p fork/src
cp -r "$osgeo4w/src/setup" fork/src/setup
# Windows git checked the sources out with CRLF; the patches have LF
grep -rlI $'\r' fork/src | xargs -r sed -i 's/\r$//'
cd fork
git init -q .
for p in "$@"; do
  echo "applying $p"
  git apply --whitespace=nowarn "$p"
done
cd ..

rm -rf build
cmake -G Ninja -S fork/src/setup -B build \
  -DCMAKE_SYSTEM_NAME=Windows \
  -DCMAKE_C_COMPILER=x86_64-w64-mingw32-gcc \
  -DCMAKE_CXX_COMPILER=x86_64-w64-mingw32-g++ \
  -DCMAKE_RC_COMPILER=x86_64-w64-mingw32-windres \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_FLAGS_RELEASE="-O2" -DCMAKE_CXX_FLAGS_RELEASE="-O2" \
  -DCMAKE_CXX_STANDARD=17 \
  -DCMAKE_EXE_LINKER_FLAGS="-static" \
  -DZLIB_SRC="$work/zlib-$ZLIB" -DBZIP2_SRC="$work/bzip2-$BZIP2"
cmake --build build 2>&1 | tail -n 300 > build/make.log || { cat build/make.log; exit 1; }
cp build/osgeo4w-setup.exe "$out"
ls -l "$out"
