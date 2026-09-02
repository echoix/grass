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

# Clang ships omp.h in its resource-dir instead of /usr/include, so
# configure's plain omp.h check misses it. Point configure at both the
# include and (from apt libomp-dev) the runtime lib. Shared by both
# clang-based coverage mechanisms below.
configure_clang_openmp_args() {
    CLANG_RES_DIR="$(clang -print-resource-dir 2>/dev/null || true)"
    if [ -n "${CLANG_RES_DIR}" ] && [ -d "${CLANG_RES_DIR}/include" ]; then
        OPENMP_ARGS+=("--with-openmp-includes=${CLANG_RES_DIR}/include")
        # Debian's libomp-dev installs libomp.so under /usr/lib/llvm-<N>/lib,
        # not the linker's default search path, so configure's link probe for
        # omp_get_num_threads fails and it falls back to -lgomp - which clang's
        # OpenMP-instrumented code (using __kmpc_*) then can't link against.
        # The resource-dir sits at <llvm-libdir>/clang/<ver>, so its
        # grandparent is <llvm-libdir>, where libomp.so lives.
        LLVM_LIB_DIR="$(cd "${CLANG_RES_DIR}/../.." && pwd)"
        if [ -e "${LLVM_LIB_DIR}/libomp.so" ]; then
            OPENMP_ARGS+=("--with-openmp-libs=${LLVM_LIB_DIR}")
        fi
    fi
}

if [ "${GRASS_LLVM_COVERAGE:-0}" = "1" ] && [ "${GRASS_SANCOV_COVERAGE:-0}" = "1" ]; then
    echo "GRASS_LLVM_COVERAGE and GRASS_SANCOV_COVERAGE are mutually exclusive" >&2
    exit 1
fi

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
    configure_clang_openmp_args
fi

# SanitizerCoverage instrumentation, opt-in via env var, compared against
# GRASS_LLVM_COVERAGE above -- see doc/development/
# sancov_coverage_experiment.md. GRASS_SANCOV_CC selects gcc (the only
# -fsanitize-coverage= sub-option GCC 13/14 implement is trace-pc, no
# per-edge guard: confirmed empirically, see the report) or clang
# (trace-pc-guard, cheaper steady-state dedup).
#
# Unlike -fprofile-instr-generate above, -fsanitize-coverage= is not
# special-cased by either compiler's driver to auto-link a runtime, so
# utils/sancov_runtime.c is built here into a small shared library that
# every GRASS binary must link against. Naively exporting "-lsancovrt"
# through LDFLAGS or configure's $LIBS does not reliably reach every link
# GRASS's build performs: GRASS's own Make templates (Shlib.make,
# Compile.make) place $(LDFLAGS) *before* the object files (GNU ld
# resolves left to right and never revisits a library once passed, so an
# undefined reference there is never satisfied), a few special-cased
# link rules (e.g. lib/init/Makefile's echo/run targets) do not go
# through the usual $(LIBES)/$(MATHLIB) machinery those templates share
# at all, and configure's own custom library probes (LOC_CHECK_LIBS,
# used for BLAS, GDAL, PROJ, and most other optional dependencies) build
# their own bespoke compile-and-link commands rather than going through
# autoconf's usual $LIBS (confirmed empirically, in that order, each by
# a different otherwise-unrelated-looking failure: an "undefined
# reference" from ld, then a segfault when it was papered over with
# -Wl,--unresolved-symbols=ignore-all, then an unrelated-looking "unable
# to link to (C)BLAS", then a silently-unlinked etc/run).
#
# Rather than chase each of those individually, $CC/$CXX are pointed at
# a tiny wrapper that appends the runtime's -L/-l/-rpath flags to
# whatever argv it is given, verbatim, then execs the real compiler.
# That covers every link GRASS's build performs, however it constructs
# the rest of the command line, because they all ultimately invoke
# $(CC)/$(CXX) (or $(LINK), which itself defaults to $(CC)) as the
# actual compiler front-end. The same flags are harmless noise on a
# compile-only invocation (-c): gcc and clang both silently ignore
# unused -l/-L/-Wl, arguments there (confirmed empirically), so the one
# wrapper is safe to use for every invocation, compile or link, without
# needing to tell them apart -- including configure's own, so the
# instrumentation flags can go back to being set the same way
# GRASS_LLVM_COVERAGE sets them above, before ./configure runs.
if [ "${GRASS_SANCOV_COVERAGE:-0}" = "1" ]; then
    SANCOV_CC="${GRASS_SANCOV_CC:-gcc}"
    case "${SANCOV_CC}" in
    gcc)
        REAL_CC="gcc"
        REAL_CXX="g++"
        SANCOV_FLAGS="-fsanitize-coverage=trace-pc"
        ;;
    clang)
        REAL_CC="clang"
        REAL_CXX="clang++"
        SANCOV_FLAGS="-fsanitize-coverage=trace-pc-guard"
        configure_clang_openmp_args
        ;;
    *)
        echo "GRASS_SANCOV_CC must be gcc or clang, got '${SANCOV_CC}'" >&2
        exit 1
        ;;
    esac

    SANCOV_RUNTIME_DIR="${PWD}/sancov-runtime"
    mkdir -p "${SANCOV_RUNTIME_DIR}"
    "${REAL_CC}" -O2 -fPIC -shared -pthread \
        -o "${SANCOV_RUNTIME_DIR}/libsancovrt.so" \
        utils/sancov_runtime.c -ldl

    cat > "${SANCOV_RUNTIME_DIR}/cc-wrapper.sh" <<EOF
#!/usr/bin/env bash
exec "${REAL_CC}" "\$@" -L"${SANCOV_RUNTIME_DIR}" -lsancovrt -Wl,-rpath,"${SANCOV_RUNTIME_DIR}"
EOF
    cat > "${SANCOV_RUNTIME_DIR}/cxx-wrapper.sh" <<EOF
#!/usr/bin/env bash
exec "${REAL_CXX}" "\$@" -L"${SANCOV_RUNTIME_DIR}" -lsancovrt -Wl,-rpath,"${SANCOV_RUNTIME_DIR}"
EOF
    chmod +x "${SANCOV_RUNTIME_DIR}/cc-wrapper.sh" "${SANCOV_RUNTIME_DIR}/cxx-wrapper.sh"
    export CC="${SANCOV_RUNTIME_DIR}/cc-wrapper.sh"
    export CXX="${SANCOV_RUNTIME_DIR}/cxx-wrapper.sh"
    export CFLAGS="${CFLAGS:--O2} -g ${SANCOV_FLAGS}"
    export CXXFLAGS="${CXXFLAGS:--O2} -g ${SANCOV_FLAGS}"
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
