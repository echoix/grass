#!/usr/bin/env bash

# Merge LLVM source-based coverage .profraw files into a single .profdata,
# then export lcov for Codecov. Run from CI after all test steps, but
# generic enough to invoke by hand too: build with GRASS_LLVM_COVERAGE=1
# (see build_ubuntu-24.04.sh), run tests with LLVM_PROFILE_FILE pointed at
# a raw dir (see pytest.yml's "Prepare coverage directories" step), then
# run this script from the repository root with a `grass` matching that
# build on PATH.
#
# Inputs (env), all optional:
#   INITIAL_PWD    - repository working directory (default: pwd)
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
# for a given input set. The per-process "%p-%9m" naming can produce
# hundreds of thousands of .profraw files in a full test run, so pass them
# via -f (a newline-separated list) rather than shell-globbing them onto
# argv, which overflows the OS argument-list limit ("Argument list too
# long").
PROFRAW_LIST="$(mktemp)"
trap 'rm -f "${PROFRAW_LIST}"' EXIT
find "${RAW_DIR}" -name '*.profraw' -print > "${PROFRAW_LIST}"
llvm-profdata merge -sparse -f "${PROFRAW_LIST}" -o "${OUT_PROFDATA}"

# Enumerate every instrumented ELF binary and shared library the install
# produced. find -perm -u+x also sweeps in executable Python and shell
# scripts, so filter to the ELF magic bytes before passing to llvm-cov.
OBJ_ARGS=()
while IFS= read -r -d '' obj; do
    magic=$(head -c4 "${obj}" 2>/dev/null | od -An -tx1 | tr -d ' \n')
    if [ "${magic}" = "7f454c46" ]; then
        OBJ_ARGS+=(-object "${obj}")
    fi
done < <(
    find "${GISBASE}" \
        \( -type f -perm -u+x -o -name '*.so' -o -name '*.so.*' \) \
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
    -ignore-filename-regex='(^/opt/|^/usr/|/\.cache/|/bin\.[^/]+/|/dist\.[^/]+/|/OBJ\.[^/]+/)' \
    "${OBJ_ARGS[@]}" \
    > "${OUT_LCOV}"

echo "llvm_coverage_export: wrote ${OUT_LCOV}"
du -sh "${OUT_PROFDATA}" "${OUT_LCOV}"
