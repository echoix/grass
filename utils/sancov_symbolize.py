#!/usr/bin/env python3
"""Aggregate GRASS_SANCOV_COVERAGE per-process dump files into a coarse,
per-file line-hit-count report.

Each dump file (written by utils/sancov_runtime.c's destructor) is a list
of "<module-path> <hex-offset>" lines, one per unique edge hit by that
process. This script resolves every (module, offset) pair to a file:line
with addr2line -i (inline-aware, so an edge inlined from a header or from
a different call site is attributed to the actual source line it came
from, not just the function's own definition line -- see the "Coverage
report quality" section of doc/development/sancov_coverage_experiment.md
for why -i matters here) and counts, per source file, how many distinct
covered lines were seen versus how many total lines the file has.

This is deliberately coarser than the lcov output
utils/llvm_coverage_export.sh produces from source-based coverage: it
reports line reached/not-reached, not per-region hit counts, and it
cannot distinguish two macro expansions that the compiler placed in the
same basic block (see the report). It exists to make SanitizerCoverage's
output comparable in spirit to lcov, not to replace it.
"""

import argparse
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def addr2line_batch(module, offsets, addr2line):
    """Resolve each offset to its innermost file:line, via one addr2line
    invocation for the whole batch.

    -i can expand a single address into several (function, file:line)
    pairs, one per inline frame, with no delimiter between one address's
    pairs and the next address's -- so -a is added purely to get the
    address itself echoed back as that delimiter.
    """
    if not offsets:
        return {}
    addrs = [f"0x{off}" for off in offsets]
    proc = subprocess.run(
        [addr2line, "-e", module, "-f", "-C", "-i", "-a", *addrs],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = proc.stdout.splitlines()
    # addr2line echoes -a addresses zero-padded to 16 hex digits, so compare
    # by numeric value rather than exact string.
    addr_values = {int(a, 16) for a in addrs}
    result = {}
    current_offset = None
    i = 0
    while i < len(lines):
        try:
            value = int(lines[i], 16)
        except ValueError:
            value = None
        if value in addr_values:
            current_offset = format(value, "x")
            i += 1
            continue
        # function line followed by file:line line; keep only the first
        # (innermost) pair seen for the current address.
        loc = lines[i + 1]
        i += 2
        if current_offset is not None and current_offset not in result:
            result[current_offset] = loc
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump_dir", help="directory of sancov-*.txt dumps")
    parser.add_argument(
        "--addr2line", default="addr2line", help="addr2line binary to use"
    )
    parser.add_argument(
        "--ignore-path-substring",
        action="append",
        default=[],
        help="skip modules whose path contains this substring "
        "(repeatable), e.g. /usr/ to drop system libraries",
    )
    args = parser.parse_args()

    dump_dir = Path(args.dump_dir)
    by_module = defaultdict(set)
    for dump_file in dump_dir.glob("sancov-*.txt"):
        for line in dump_file.read_text().splitlines():
            module, offset = line.split()
            if any(s in module for s in args.ignore_path_substring):
                continue
            by_module[module].add(offset)

    hits_by_file = defaultdict(set)
    for module, offsets in by_module.items():
        # A module can be gone by the time this runs: e.g. a test that
        # builds a GRASS addon into a temporary directory via
        # g.extension cleans that directory up once the test finishes,
        # well before this post-test symbolization step -- confirmed on
        # a real CI run, where an addon binary under a pytest tmp_path
        # was recorded as a module but no longer existed. Skip it rather
        # than letting one vanished module abort the whole run.
        if not Path(module).exists():
            print(
                f"sancov_symbolize: skipping vanished module {module}", file=sys.stderr
            )
            continue
        resolved = addr2line_batch(module, sorted(offsets), args.addr2line)
        for loc in resolved.values():
            if loc in ("??:0", "??:?"):
                continue
            file_part, _, line_part = loc.rpartition(":")
            if not file_part or not line_part.split()[0].isdigit():
                continue
            hits_by_file[file_part].add(int(line_part.split()[0]))

    for file_name in sorted(hits_by_file):
        lines_hit = hits_by_file[file_name]
        print(f"{file_name}: {len(lines_hit)} distinct lines hit")


if __name__ == "__main__":
    sys.exit(main())
