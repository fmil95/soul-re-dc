#!/usr/bin/env python3
"""Create src/<file>.c for every file in config/functions.csv, with one INCLUDE_ASM per function.

Each C file includes its own header, include/<file>.h. Headers imported from soul-re
(tools/import_psx_headers.py) are used as they are; a minimal header is created for files that have none
(the DC-only files).

Existing C files are never overwritten (they may contain decompiled code). For an existing file the tool only
reports functions from the CSV that it neither defines nor INCLUDE_ASMs. With --fix-includes, an existing
file's `#include "common.h"` line is replaced with its own header.

Usage: gen_c.py [--functions config/functions.csv] [--src src] [--include include] [--fix-includes]
"""
import argparse
import collections
import csv
import os
import re


def header_guard(fl):
    return "_" + re.sub(r"[^A-Za-z0-9]", "_", fl).upper() + "_H_"


def ensure_header(inc_root, fl):
    path = os.path.join(inc_root, fl + ".h")
    if os.path.exists(path):
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    g = header_guard(fl)
    with open(path, "w", newline="\n") as f:
        f.write(f"#ifndef {g}\n#define {g}\n\n#include \"common.h\"\n\n#endif\n")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--functions", default="config/functions.csv")
    ap.add_argument("--src", default="src")
    ap.add_argument("--include", default="include")
    ap.add_argument("--fix-includes", action="store_true")
    a = ap.parse_args()

    by_file = collections.OrderedDict()
    psx = {}
    with open(a.functions) as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            by_file.setdefault(r["file"], []).append((int(r["addr"], 16), r["name"]))
            psx.setdefault(r["file"], r["psx_file"])

    created = headers = fixed = 0
    for fl, funcs in by_file.items():
        headers += ensure_header(a.include, fl)
        own = f'#include "{fl}.h"'
        path = os.path.join(a.src, fl + ".c")
        if os.path.exists(path):
            text = open(path).read()
            if a.fix_includes and '#include "common.h"' in text:
                text = text.replace('#include "common.h"', own, 1)
                with open(path, "w", newline="\n") as f:
                    f.write(text)
                fixed += 1
            missing = [n for _, n in funcs if not re.search(r"\b%s\b" % re.escape(n), text)]
            if missing:
                print(f"{path}: not referenced: {', '.join(missing)}")
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        lo = funcs[0][0]
        origin = f"PSX: src/{psx[fl]}.c" if psx[fl] else "DC-only (no PSX counterpart found)"
        lines = [f"/* DC {lo:08X}, {len(funcs)} functions. {origin} */", own, ""]
        lines += [f'INCLUDE_ASM("asm/nonmatchings/{fl}", {n});' for _, n in funcs]
        with open(path, "w", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        created += 1
    print(f"{created} C files created, {headers} headers created, {fixed} C files switched to their own header")


if __name__ == "__main__":
    main()
