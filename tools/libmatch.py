#!/usr/bin/env python3
"""Find KATANA SDK library objects inside 1ST_READ.BIN.

For every object in the given .a archives / .obj files, each allocated section with contents is searched
for in the binary with relocated bytes masked out. Prints a CSV-ish table of matches sorted by address.

Usage: libmatch.py rom/1ST_READ.BIN KATANA/Lib/Gnu/*.a KATANA/Lib/Gnu/*.obj [--base 0x8c010000]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from elfobj import ElfObject, read_archive  # noqa: E402

SHF_ALLOC = 2
ANCHOR = 16  # bytes of fixed data used to seed the search


def find_all(binary, data, mask, align):
    n = len(data)
    if n == 0:
        return []
    # fixed (unrelocated) spans
    spans, i = [], 0
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            spans.append((i, j))
            i = j
        else:
            i += 1
    # anchor: the fixed window of up to 32 bytes with the most distinct byte values
    best = None
    for s, e in spans:
        for w in range(s, max(s + 1, e - ANCHOR + 1), 8):
            win = data[w:min(e, w + 32)]
            if len(win) < min(ANCHOR, n):
                continue
            score = len(set(win))
            if best is None or score > best[0]:
                best = (score, w, win)
    if best is None or best[0] < 6:
        return None  # too little distinctive fixed data to identify reliably
    _, aoff, anchor = best
    hits, pos = [], binary.find(anchor)
    while pos >= 0:
        base = pos - aoff
        if base >= 0 and base % align == 0 and base + n <= len(binary):
            if all(binary[base + s:base + e] == data[s:e] for s, e in spans):
                hits.append(base)
        pos = binary.find(anchor, pos + 1)
    return hits


def objects(paths):
    for p in paths:
        if p.lower().endswith(".a"):
            for name, blob in read_archive(p):
                yield os.path.basename(p), name, blob
        else:
            with open(p, "rb") as f:
                yield "", os.path.basename(p), f.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("binary")
    ap.add_argument("libs", nargs="+")
    ap.add_argument("--base", type=lambda x: int(x, 0), default=0x8C010000)
    ap.add_argument("--min-size", type=int, default=32)
    a = ap.parse_args()

    binary = open(a.binary, "rb").read()
    rows, ambiguous, missing = [], [], 0
    for lib, member, blob in objects(a.libs):
        try:
            obj = ElfObject(member, blob)
        except ValueError as e:
            print(f"# skip {lib}:{member}: {e}", file=sys.stderr)
            continue
        for sec in obj.sections:
            if not (sec.flags & SHF_ALLOC) or not sec.data or sec.size < a.min_size:
                continue
            hits = find_all(binary, sec.data, obj.mask(sec), max(1, min(sec.align or 1, 4)))
            if hits is None:
                continue
            if not hits:
                missing += 1
                continue
            if len(hits) > 1:
                ambiguous.append((lib, member, sec.name, hits))
            for h in hits:
                rows.append((h + a.base, sec.size, lib, member, sec.name, len(hits)))
    rows.sort()
    for addr, size, lib, member, sec, n in rows:
        flag = "" if n == 1 else f"  (x{n})"
        print(f"{addr:08x} {addr + size:08x} {size:7x} {lib}:{member}:{sec}{flag}")
    print(f"# {len(rows)} placements, {len(ambiguous)} ambiguous sections, {missing} sections not found",
          file=sys.stderr)


if __name__ == "__main__":
    main()
