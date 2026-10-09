#!/bin/bash
# Builds Cygwin's setup (pinned upstream SHA, plus an optional patch series)
# with the MSYS2 mingw-w64 toolchain, running in an MSYS2 MINGW64 shell.
#
# usage: build_upstream.sh <source dir> <build dir> <output exe> [patch dir]
set -euo pipefail

# Only Cygwin's own tools: the runner image has other mingw-w64 toolchains on PATH.
export PATH=/usr/bin:/usr/local/bin:/bin
# the checkout was made by Windows git, as a different user than Cygwin sees
git config --global --add safe.directory "*"

src=$1
bld=$2
out=$3
patches=${4:-}

if [ -n "$patches" ]; then
  git -C "$src" config user.email bench@example.invalid
  git -C "$src" config user.name bench
  for p in "$patches"/*.diff; do
    echo "applying $p"
    git -C "$src" apply --whitespace=nowarn "$p"
  done
fi

cd "$src"
x86_64-w64-mingw32-g++ --version | head -1
export ACLOCAL_PATH=$(x86_64-w64-mingw32-g++ --print-sysroot)/mingw/share/aclocal
NOCONFIGURE=1 ./bootstrap.sh --host=x86_64-w64-mingw32

rm -rf "$bld"
mkdir -p "$bld"
cd "$bld"
# -Werror from upstream's Makefile.am is kept for the unmodified upstream build
# but dropped for the patched ones (new compiler warnings must not fail them).
"$src/configure" --host=x86_64-w64-mingw32 --target=x86_64-w64-mingw32 2>&1 | tail -30
make -j"$(nproc)" setup.exe V=1 2>&1 | tail -n 400 > make.log || { cat make.log; exit 1; }
cp setup.exe "$out"
ls -l "$out"
