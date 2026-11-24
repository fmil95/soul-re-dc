#!/usr/bin/env python3
"""Create src/<file>.c for every file in config/functions.csv, with one INCLUDE_ASM per function.

Existing C files are never overwritten (they may contain decompiled code). For an existing file the tool only
reports functions from the CSV that the file neither defines nor INCLUDE_ASMs.

Usage: gen_c.py [--functions config/functions.csv] [--src src]
"""
import argparse
import collections
import csv
import os
import re


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--functions", default="config/functions.csv")
    ap.add_argument("--src", default="src")
    a = ap.parse_args()

    by_file = collections.OrderedDict()
    psx = {}
    with open(a.functions) as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            by_file.setdefault(r["file"], []).append((int(r["addr"], 16), r["name"]))
            psx.setdefault(r["file"], r["psx_file"])

    created = 0
    for fl, funcs in by_file.items():
        path = os.path.join(a.src, fl + ".c")
        if os.path.exists(path):
            text = open(path).read()
            missing = [n for _, n in funcs if not re.search(r"\b%s\b" % re.escape(n), text)]
            if missing:
                print(f"{path}: not referenced: {', '.join(missing)}")
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        lo = funcs[0][0]
        origin = f"PSX: src/{psx[fl]}.c" if psx[fl] else "DC-only (no PSX counterpart found)"
        lines = [
            f"/* DC {lo:08X}, {len(funcs)} functions. {origin} */",
            '#include "common.h"',
            "",
        ]
        lines += [f'INCLUDE_ASM("asm/nonmatchings/{fl}", {n});' for _, n in funcs]
        with open(path, "w", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        created += 1
    print(f"{created} C files created, {len(by_file) - created} already existed")


if __name__ == "__main__":
    main()
