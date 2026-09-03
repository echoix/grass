#!/usr/bin/env bash

# Print disk usage of raw coverage artifacts before combining. Emitted to
# the CI log so we can watch it approach the runner storage budget.

set -u

: "${INITIAL_PWD:=$(pwd)}"
: "${RAW_DIR:=${INITIAL_PWD}/llvm-cov-raw}"

echo "=== LLVM .profraw files ==="
if [ -d "${RAW_DIR}" ]; then
    count=$(find "${RAW_DIR}" -name '*.profraw' -type f | wc -l | tr -d ' ')
    echo "count: ${count}"
    du -sh "${RAW_DIR}" 2>/dev/null || true
else
    echo "no ${RAW_DIR} (build was not instrumented, or no tests ran)"
fi

echo "=== Python coverage.py partial files ==="
py_count=$(find "${INITIAL_PWD}" -maxdepth 2 -name '.coverage.*' -type f 2>/dev/null \
    | wc -l | tr -d ' ')
echo "count: ${py_count}"
if [ "${py_count}" -gt 0 ]; then
    du -sch "${INITIAL_PWD}"/.coverage.* 2>/dev/null | tail -1
fi

echo "=== Filesystem ==="
df -h "${INITIAL_PWD}" 2>/dev/null || df -h
