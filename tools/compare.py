#!/usr/bin/env python3
"""Compare a built binary against the original; report the first differing addresses per segment.

Usage: compare.py config/1st_read.toml build/1ST_READ.BIN
"""
import hashlib
import sys
import tomllib


def main():
    with open(sys.argv[1], "rb") as f:
        cfg = tomllib.load(f)
    b = cfg["binary"]
    orig = open(b["rom"], "rb").read()
    built = open(sys.argv[2], "rb").read()
    sha = hashlib.sha1(built).hexdigest()
    if sha == b["sha1"]:
        print(f"{sys.argv[2]}: OK (sha1 {sha})")
        return 0
    print(f"{sys.argv[2]}: MISMATCH (sha1 {sha}, size {len(built):#x} vs {len(orig):#x})")
    vram, segs = b["vram"], cfg["segment"]
    for i, s in enumerate(segs):
        lo = s["start"] - vram
        hi = (segs[i + 1]["start"] - vram) if i + 1 < len(segs) else len(orig)
        diffs = [o for o in range(lo, hi) if o >= len(built) or built[o] != orig[o]]
        if diffs:
            print(f"  {s['name']}: {len(diffs)} bytes differ, first at {diffs[0] + vram:08X}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
