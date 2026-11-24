#!/usr/bin/env python3
"""Assign every DC game function to a source file and a name -> config/functions.csv.

Inputs: the ROM and config/psx_match.csv (from tools/psx_match.py).

File boundaries:
  * ld pads between object files with zeros, while gas pads between functions inside one object with
    nops (0x0009). A function start preceded by 0x0000 therefore begins a new object file.
  * Where two different PSX-labelled runs meet with no zero padding (the previous object happened to end
    32-byte aligned), the file is cut at the first function of the second run.
Each resulting file takes the PSX file most of its matched functions came from; files with no PSX match
are DC-only and named dc/unk_<ADDR>.

Function names: PSX name when the function matched a PSX function of the file it was assigned to,
otherwise func_<ADDR>.

Usage: gen_functions.py [--rom rom/1ST_READ.BIN] [--match config/psx_match.csv] [--out config/functions.csv]
The output is meant to be edited by hand afterwards (renames, re-splits); re-running overwrites it.
"""
import argparse
import collections
import csv
import struct

VRAM = 0x8C010000
GAME_TEXT = (0x8C05AC20, 0x8C12A9E0)
PUSHES = {0x2F86, 0x2F96, 0x2FA6, 0x2FB6, 0x2FC6, 0x2FD6, 0x2FE6, 0x4F22}  # mov.l rN,@-r15 / sts.l pr


def dc_path(psx_file):
    """Map a PSX source path to its DC location."""
    if psx_file.startswith("Overlays/"):
        name = psx_file.split("/")[-1].upper()
        if name == "MCARDX":
            return "Game/MCARD/MCARDX"
        if name == "CINEMAX":
            return "Game/CINEMA/CINEMAX"
        return f"Game/MONSTER/{name}"  # on DC the monster overlays are linked into MONSTER/, alphabetically
    return psx_file


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="rom/1ST_READ.BIN")
    ap.add_argument("--match", default="config/psx_match.csv")
    ap.add_argument("--out", default="config/functions.csv")
    a = ap.parse_args()
    rom = open(a.rom, "rb").read()

    def hw(addr):
        return struct.unpack_from("<H", rom, addr - VRAM)[0]

    rows = {int(r["dc_addr"], 16): r for r in csv.DictReader(open(a.match))}

    # extra function starts the pointer scan cannot see (never called / referenced): a 32-byte aligned
    # address after padding that starts with a register push
    starts = set(rows)
    for addr in range(GAME_TEXT[0] + 32, GAME_TEXT[1], 32):
        if addr not in starts and hw(addr - 2) in (0x0009, 0x0000) and hw(addr) in PUSHES:
            starts.add(addr)
    funcs = sorted(starts)
    extra = len(funcs) - len(rows)

    label = {}
    for f in funcs:
        r = rows.get(f)
        label[f] = r["psx_file"] if r and r["psx_file"] and r["outlier"] == "0" else None

    def nearest(i, step):
        while 0 <= i < len(funcs):
            if label[funcs[i]]:
                return label[funcs[i]]
            i += step
        return None

    # 1. cut at zero padding (ld fill between objects)
    cuts = set()
    for i, f in enumerate(funcs[1:], 1):
        if hw(f - 2) == 0x0000:
            before, after = nearest(i - 1, -1), nearest(i, 1)
            if before != after or before is None:
                cuts.add(i)
    segs, cur = [], []
    for i, f in enumerate(funcs):
        if i in cuts and cur:
            segs.append(cur)
            cur = []
        cur.append(f)
    segs.append(cur)

    # 2. split segments where two well-supported PSX files meet without padding
    final = []
    for seg in segs:
        counts = collections.Counter(label[f] for f in seg if label[f])
        strong = {fl for fl, n in counts.items() if n >= 2}
        if len(strong) <= 1:
            final.append(seg)
            continue
        cur, cur_file = [], None
        for f in seg:
            fl = label[f]
            if fl in strong and fl != cur_file:
                if cur_file is not None and cur:
                    final.append(cur)
                    cur = []
                cur_file = fl
            cur.append(f)
        final.append(cur)

    # 3. name files; a PSX file split over several DC objects keeps its name on the best-supported one
    seg_file = []
    for seg in final:
        counts = collections.Counter(label[f] for f in seg if label[f])
        seg_file.append(counts.most_common(1)[0] if counts else (None, 0))
    best = {}
    for i, (fl, n) in enumerate(seg_file):
        if fl and n > best.get(fl, (-1, 0))[1]:
            best[fl] = (i, n)
    names_used = collections.Counter()
    out = []
    for i, seg in enumerate(final):
        fl, n = seg_file[i]
        if fl and best[fl][0] == i:
            path = dc_path(fl)
        elif fl:
            path = f"{dc_path(fl)}_{seg[0]:08X}"
        else:
            path = f"dc/unk_{seg[0]:08X}"
        for f in seg:
            r = rows.get(f)
            name = None
            if r and r["psx_name"] and r["outlier"] == "0" and r["psx_file"] == fl:
                name = r["psx_name"]
            if not name:
                name = f"func_{f:08X}"
            if names_used[name]:
                name = f"{name}_{f:08X}"
            names_used[name] += 1
            psx_hint = r["psx_name"] if r and r["psx_name"] and name.startswith("func_") else ""
            out.append((f, path, name, fl or "", psx_hint))

    with open(a.out, "w", newline="\n") as fh:
        fh.write("# DC game functions in link order. Edit freely: file = src/<file>.c, name = symbol.\n")
        fh.write("# psx_file: PSX file this DC file was matched to. psx_hint: weak/outlier PSX match for func_ names.\n")
        fh.write("addr,file,name,psx_file,psx_hint\n")
        for f, path, name, fl, hint in out:
            fh.write(f"{f:08X},{path},{name},{fl},{hint}\n")

    files = list(dict.fromkeys(p for _, p, *_ in out))
    named = sum(1 for o in out if not o[2].startswith("func_"))
    print(f"{len(funcs)} functions ({extra} found by prologue scan), {len(files)} files "
          f"({sum(1 for p in files if p.startswith('dc/'))} DC-only), {named} named from PSX -> {a.out}")


if __name__ == "__main__":
    main()
