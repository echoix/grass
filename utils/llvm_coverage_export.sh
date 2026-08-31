#!/usr/bin/env bash

# Merge LLVM source-based coverage .profraw files into a single .profdata,
# then export lcov for Codecov. Invoked from CI after all test steps.
#
# Inputs (env):
#   INITIAL_PWD    - repository working directory (must match .coveragerc)
#   RAW_DIR        - directory holding *.profraw (default: $INITIAL_PWD/llvm-cov-raw)
#   OUT_PROFDATA   - merged profdata output (default: $INITIAL_PWD/grass.profdata)
#   OUT_LCOV       - lcov output for Codecov (default: $INITIAL_PWD/coverage-llvm.lcov)
#   GISBASE        - installed GRASS prefix; falls back to `grass --config path`
#
# Requires llvm-profdata and llvm-cov on PATH matching the clang used to build.

set -euo pipefail

: "${INITIAL_PWD:=$(pwd)}"
: "${RAW_DIR:=${INITIAL_PWD}/llvm-cov-raw}"
: "${OUT_PROFDATA:=${INITIAL_PWD}/grass.profdata}"
: "${OUT_LCOV:=${INITIAL_PWD}/coverage-llvm.lcov}"
: "${GISBASE:=$(grass --config path)}"

if ! compgen -G "${RAW_DIR}/*.profraw" > /dev/null; then
    echo "llvm_coverage_export: no .profraw files under ${RAW_DIR}; nothing to export."
    : > "${OUT_LCOV}"
    exit 0
fi

# -sparse drops zero-count regions so merges are smaller and deterministic
# for a given input set.
llvm-profdata merge -sparse -o "${OUT_PROFDATA}" "${RAW_DIR}"/*.profraw

# Enumerate every instrumented binary and shared library the install produced.
# On macOS the tools are Mach-O executables plus *.dylib; on Linux ELF plus *.so.
OBJ_ARGS=()
while IFS= read -r -d '' obj; do
    # Filter to real binaries (ELF on Linux, Mach-O on macOS). find -perm -u+x
    # sweeps in executable Python and shell scripts, which llvm-cov rejects.
    magic=$(head -c4 "${obj}" 2>/dev/null | od -An -tx1 | tr -d ' \n')
    case "${magic}" in
        7f454c46)         OBJ_ARGS+=(-object "${obj}") ;;         # ELF
        cffaedfe|cafebabe|feedface|feedfacf) \
                          OBJ_ARGS+=(-object "${obj}") ;;         # Mach-O
    esac
done < <(
    find "${GISBASE}" \
        \( -type f -perm -u+x \
           -o -name '*.dylib' -o -name '*.so' -o -name '*.so.*' \) \
        -print0
)

if [ "${#OBJ_ARGS[@]}" -eq 0 ]; then
    echo "llvm_coverage_export: no instrumented objects found under ${GISBASE}." >&2
    exit 1
fi

# Drop system, conda, and build-tree paths so Codecov only sees repo files.
llvm-cov export \
    -format=lcov \
    -instr-profile="${OUT_PROFDATA}" \
    -ignore-filename-regex='(^/opt/|^/usr/|/conda-|/miniconda|/micromamba|/\.cache/|/bin\.[^/]+/|/dist\.[^/]+/|/OBJ\.[^/]+/)' \
    "${OBJ_ARGS[@]}" \
    > "${OUT_LCOV}"

echo "llvm_coverage_export: wrote ${OUT_LCOV}"
du -sh "${OUT_PROFDATA}" "${OUT_LCOV}"
