"""Compare decompression speed of bz2 with xz and zstd on the same tar."""

import bz2
import lzma
import sys
import time

import zstandard


def best_of(func, reps=3):
    best = None
    for _ in range(reps):
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        best = elapsed if best is None else min(best, elapsed)
    return best


print("| package | format | size MB | decode s | decode MB/s (tar) |")
print("|---|---|---|---|---|")
for path in sys.argv[1:]:
    with open(path, "rb") as f:
        data_bz2 = f.read()
    raw = bz2.decompress(data_bz2)
    data_xz = lzma.compress(raw, preset=6)
    data_zst = zstandard.ZstdCompressor(level=19, threads=-1).compress(raw)
    mb = len(raw) / 1e6
    name = path.replace("\\", "/").rsplit("/", 1)[-1]
    for label, data, func in (
        ("bz2", data_bz2, lambda: bz2.decompress(data_bz2)),
        ("xz -6", data_xz, lambda: lzma.decompress(data_xz)),
        (
            "zstd -19",
            data_zst,
            lambda: zstandard.ZstdDecompressor().decompress(
                data_zst, max_output_size=len(raw) + 1
            ),
        ),
    ):
        secs = best_of(func)
        print(
            f"| {name} | {label} | {len(data) / 1e6:.1f} | {secs:.2f} "
            f"| {mb / secs:.0f} |"
        )
