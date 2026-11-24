#!/usr/bin/env python3
"""Import headers from the PSX decomp (soul-re) into include/.

Copies:
  include/Game/**/*.h              -> include/Game/**/*.h           (as is)
  include/Overlays/<n>/<n>.h       -> include/<DC path>.h          (e.g. Game/MONSTER/ALUKA.h)
  include/Libs/SDK.h, STRING.h     -> include/Libs/
#include lines that name an overlay header are rewritten to its DC path.

Not imported (PSX/MIPS-only or replaced by a DC version): common.h, include_asm.h, Libs/STDARG.h (the SH
varargs ABI needs the compiler's <stdarg.h>), Libs/GTE.h and Libs/gte_macros.h (MIPS COP2 inline asm).

Existing files are skipped unless --force, since imported headers get DC-specific edits afterwards.
Usage: import_psx_headers.py --psx ~/soul-re [--force]
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_functions import dc_path  # noqa: E402

INC = re.compile(r'^(\s*#\s*include\s*")Overlays/([^/"]+)/([^/"]+)\.h(")', re.M)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--psx", required=True)
    ap.add_argument("--out", default="include")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    src_inc = os.path.join(a.psx, "include")

    jobs = []
    for root, _dirs, files in os.walk(os.path.join(src_inc, "Game")):
        for f in files:
            if f.endswith(".h"):
                p = os.path.join(root, f)
                jobs.append((p, os.path.relpath(p, src_inc).replace(os.sep, "/")))
    ov = os.path.join(src_inc, "Overlays")
    for name in sorted(os.listdir(ov)):
        p = os.path.join(ov, name, name + ".h")
        if os.path.exists(p):
            jobs.append((p, dc_path(f"Overlays/{name}/{name}") + ".h"))
    for f in ("SDK.h", "STRING.h"):
        jobs.append((os.path.join(src_inc, "Libs", f), f"Libs/{f}"))

    copied = skipped = 0
    for src, rel in sorted(jobs, key=lambda j: j[1]):
        dst = os.path.join(a.out, rel)
        if os.path.exists(dst) and not a.force:
            skipped += 1
            continue
        text = open(src, encoding="latin1").read()
        text = INC.sub(lambda m: f"{m.group(1)}{dc_path(f'Overlays/{m.group(2)}/{m.group(3)}')}.h{m.group(4)}", text)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="latin1", newline="\n") as fh:
            fh.write(text.replace("\r\n", "\n"))
        copied += 1
    print(f"{copied} headers imported, {skipped} already present")


if __name__ == "__main__":
    main()
