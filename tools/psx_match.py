#!/usr/bin/env python3
"""Match DC game functions to PSX (soul-re) functions, and from that recover the DC file splits.

Features used (all survive the MIPS -> SH4 port):
  * string literals each function references (by content)
  * calls to C library functions (sprintf, strcpy, ...), identified on DC via the SDK libc/libgcc objects
  * the call graph: callees of matched functions are aligned in call order
  * file contiguity: functions keep their source order inside a file on both platforms

Usage: psx_match.py --psx ~/soul-re [--rom rom/1ST_READ.BIN] [--katana KATANA]
Outputs build/psx_match.csv (one row per DC function) and build/psx_splits.txt (per-file ranges).
"""
import argparse
import bisect
import collections
import glob
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from elfobj import ElfObject, read_archive  # noqa: E402
import libmatch  # noqa: E402

VRAM = 0x8C010000
GAME_TEXT = (0x8C05AC20, 0x8C12A9E0)
LIB_TEXT = (0x8C12A9E0, 0x8C138100)
DATA_START = 0x8C138100
PSX_GP = 0x800D7598
MIN_STR = 4

LIBC_NAMES = {
    "sprintf", "printf", "puts", "strcpy", "strncpy", "strcat", "strlen", "strcmp", "strncmp", "strchr",
    "strrchr", "strpbrk", "strtok", "strstr", "memset", "memcpy", "memmove", "memcmp", "memchr", "rand",
    "srand", "abs", "labs", "atoi", "atol", "strtol", "toupper", "tolower", "qsort", "sqrt", "rsin", "rcos",
}


def printable_at(buf, off):
    end = buf.find(b"\0", off)
    if end < 0 or end - off < MIN_STR:
        return None
    s = buf[off:end]
    if all(32 <= c < 127 or c in (9, 10, 13) for c in s):
        return s.decode("latin1")
    return None


# ----------------------------------------------------------------------------------------- PSX

class PsxFunc:
    __slots__ = ("key", "name", "addr", "size", "file", "callees", "strings", "callers", "index")

    def __init__(self, key, name, addr, size):
        self.key, self.name, self.addr, self.size = key, name, addr, size
        self.file, self.callees, self.strings, self.callers, self.index = None, [], [], set(), -1


def psx_file_ranges(root):
    """(elf_name, start, end, file) for every .text input section in build/*.map."""
    out = []
    for mp in glob.glob(os.path.join(root, "build", "*.map")):
        elf = os.path.basename(mp)[:-4]
        for line in open(mp, encoding="latin1"):
            m = re.match(r"^ \.text\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+\S*build/(?:src|asm)/(\S+)\.[cs]\.o", line)
            if m and int(m.group(2), 16):
                a = int(m.group(1), 16)
                out.append((elf, a, a + int(m.group(2), 16), m.group(3)))
    return out


def load_psx(root):
    elfs = {}
    for p in glob.glob(os.path.join(root, "build", "*.elf")):
        elfs[os.path.basename(p)[:-4]] = ElfObject(p, open(p, "rb").read())
    ranges = psx_file_ranges(root)
    funcs = {}
    for en, e in elfs.items():
        for name, val, size, info, shn in e.symbols:
            if info & 0xF == 2 and size and shn < len(e.sections):
                funcs[(en, val)] = PsxFunc((en, val), name, val, size)
    for f in funcs.values():
        for en, lo, hi, fl in ranges:
            if en == f.key[0] and lo <= f.addr < hi:
                f.file = fl
                break

    def mem(en, addr):
        for e in (elfs[en], elfs["KAIN2"]):
            for s in e.sections:
                if s.flags & 2 and s.data and s.addr <= addr < s.addr + len(s.data):
                    return s.data, addr - s.addr
        return None, 0

    def resolve(en, addr):
        if (en, addr) in funcs:
            return (en, addr)
        if ("KAIN2", addr) in funcs:
            return ("KAIN2", addr)
        return None

    for f in funcs.values():
        en = f.key[0]
        buf, off = mem(en, f.addr)
        if buf is None:
            continue
        regs = {28: PSX_GP, 0: 0}
        for i in range(off, min(off + f.size, len(buf)) - 3, 4):
            (w,) = struct.unpack_from("<I", buf, i)
            op, rs, rt = w >> 26, (w >> 21) & 31, (w >> 16) & 31
            imm = w & 0xFFFF
            simm = imm - 0x10000 if imm & 0x8000 else imm
            pc = f.addr + (i - off)
            if op == 3:  # jal
                tgt = (pc & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
                k = resolve(en, tgt)
                if k:
                    f.callees.append(k)
                continue
            val = None
            if op == 0xF:
                regs[rt] = (imm << 16) & 0xFFFFFFFF
                continue
            if op == 9 and rs in regs:  # addiu
                val = (regs[rs] + simm) & 0xFFFFFFFF
            elif op == 0xD and rs in regs:  # ori
                val = regs[rs] | imm
            if val is not None:
                regs[rt] = val
                b2, o2 = mem(en, val)
                if b2 is not None:
                    s = printable_at(b2, o2)
                    if s:
                        f.strings.append(s)
            elif rt in regs and op not in (0x2B, 0x29, 0x28) and rt != 28:
                regs.pop(rt, None)
    for f in funcs.values():
        for c in f.callees:
            funcs[c].callers.add(f.key)
    return funcs


# ------------------------------------------------------------------------------------------ DC

class DcFunc:
    __slots__ = ("addr", "end", "callees", "strings", "callers", "index")

    def __init__(self, addr, end):
        self.addr, self.end = addr, end
        self.callees, self.strings, self.callers, self.index = [], [], set(), -1


def dc_lib_names(rom, katana):
    """addr -> symbol name for C library functions linked into the DC binary."""
    names = {}
    gnu = os.path.join(katana, "Utl", "Dev", "Gnu")
    archives = [os.path.join(gnu, "sh-elf", "lib", "ml", "m4-single-only", "libc.a"),
                os.path.join(gnu, "sh-elf", "lib", "ml", "m4-single-only", "libm.a"),
                os.path.join(gnu, "lib", "gcc-lib", "sh-elf", "2.9-SYSDEV-sh4p2_final-991007", "ml",
                             "m4-single-only", "libgcc.a")] + glob.glob(os.path.join(katana, "Lib", "Gnu", "*.a"))
    for path in archives:
        if not os.path.exists(path):
            continue
        for member, blob in read_archive(path):
            try:
                obj = ElfObject(member, blob)
            except ValueError:
                continue
            for si, sec in enumerate(obj.sections):
                if sec.name != ".text" or not sec.data:
                    continue
                hits = libmatch.find_all(rom, sec.data, obj.mask(sec), 2)
                if not hits or len(hits) != 1:
                    continue
                for nm, val, _sz, info, shn in obj.symbols:
                    if shn == si and info >> 4 == 1 and info & 0xF in (0, 2):
                        names[VRAM + hits[0] + val] = nm.lstrip("_")
    return names


def load_dc(rom, katana):
    words = struct.unpack_from("<%dI" % (len(rom) // 4), rom)
    lo, hi = GAME_TEXT
    starts = sorted({w for w in words if lo <= w < hi and w % 32 == 0} | {lo})
    funcs = []
    for i, a in enumerate(starts):
        funcs.append(DcFunc(a, starts[i + 1] if i + 1 < len(starts) else hi))
    by_addr = {f.addr: f for f in funcs}
    libs = dc_lib_names(rom, katana)
    strings = {}
    for f in funcs:
        for pc in range(f.addr, f.end, 2):
            (op,) = struct.unpack_from("<H", rom, pc - VRAM)
            if op & 0xF000 != 0xD000:
                continue
            ea = ((pc + 4) & ~3) + (op & 0xFF) * 4
            if not (lo <= ea < hi):
                continue
            (w,) = struct.unpack_from("<I", rom, ea - VRAM)
            if w in by_addr:
                f.callees.append(w)
            elif w in libs:
                f.callees.append("lib:" + libs[w])
            elif w >= DATA_START and w < VRAM + len(rom):
                if w not in strings:
                    strings[w] = printable_at(rom, w - VRAM)
                if strings[w]:
                    f.strings.append(strings[w])
    for f in funcs:
        for c in f.callees:
            if c in by_addr:
                by_addr[c].callers.add(f.addr)
    return funcs, by_addr, libs


# ------------------------------------------------------------------------------------ matching

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--psx", required=True)
    ap.add_argument("--rom", default="rom/1ST_READ.BIN")
    ap.add_argument("--katana", default="KATANA")
    ap.add_argument("--out", default="build")
    a = ap.parse_args()

    rom = open(a.rom, "rb").read()
    psx = load_psx(a.psx)
    dcl, dc, libs = load_dc(rom, a.katana)
    print(f"# PSX {len(psx)} functions, DC {len(dcl)} functions, {len(libs)} DC library symbols")

    # PSX game functions, ordered by (file link order, address), and lib name mapping
    game = [f for f in psx.values() if f.file and not f.file.startswith("lib/")]
    psx_lib = {f.key: f.name for f in psx.values() if f.file is None or f.file.startswith("lib/")}

    def p_callees(f):
        out = []
        for c in f.callees:
            if c in psx_lib:
                if psx_lib[c] in LIBC_NAMES:
                    out.append("lib:" + psx_lib[c])
            else:
                out.append(c)
        return out

    def d_callees(f):
        return [c for c in f.callees if not (isinstance(c, str) and c[4:] not in LIBC_NAMES)]

    by_file = collections.defaultdict(list)
    for f in game:
        by_file[f.file].append(f)
    for fl in by_file:
        by_file[fl].sort(key=lambda f: f.addr)
        for i, f in enumerate(by_file[fl]):
            f.index = i
    for i, f in enumerate(dcl):
        f.index = i

    m_dp, m_pd, method = {}, {}, {}

    def add(d, p, how):
        if d in m_dp or p in m_pd:
            return False
        m_dp[d], m_pd[p], method[d] = p, d, how
        return True

    # 1. seeds: identical, distinctive string-reference sets
    def sig(strs):
        return tuple(sorted(set(strs)))
    ps, ds = collections.defaultdict(list), collections.defaultdict(list)
    for f in game:
        if f.strings:
            ps[sig(f.strings)].append(f.key)
    for f in dcl:
        if f.strings:
            ds[sig(f.strings)].append(f.addr)
    for s, pk in ps.items():
        if len(pk) == 1 and len(ds.get(s, [])) == 1 and (len(s) > 1 or len(s[0]) >= 8):
            add(ds[s][0], pk[0], "strings")
    seeds = len(m_dp)

    # 2. propagate until fixpoint
    def align(dl, pl, how):
        """Pair unknown entries between known fixed points when segment lengths agree."""
        new = 0
        dl = list(dict.fromkeys(dl))
        pl = list(dict.fromkeys(pl))
        fixed = []
        j0 = 0
        for i, d in enumerate(dl):
            tgt = d if isinstance(d, str) else m_dp.get(d)
            if tgt is None:
                continue
            try:
                j = pl.index(tgt, j0)
            except ValueError:
                continue
            fixed.append((i, j))
            j0 = j + 1
        bounds = [(-1, -1)] + fixed + [(len(dl), len(pl))]
        for (i0, j0), (i1, j1) in zip(bounds, bounds[1:]):
            seg_d, seg_p = dl[i0 + 1:i1], pl[j0 + 1:j1]
            if seg_d and len(seg_d) == len(seg_p):
                for d, p in zip(seg_d, seg_p):
                    if isinstance(d, str) or isinstance(p, str):
                        continue
                    if d not in m_dp and p not in m_pd and psx[p].file and not psx[p].file.startswith("lib/"):
                        new += add(d, p, how)
        return new

    changed = True
    while changed:
        changed = False
        for d, p in list(m_dp.items()):
            if align(d_callees(dc[d]), p_callees(psx[p]), "callee"):
                changed = True
            uc_d = [c for c in dc[d].callers if c not in m_dp]
            uc_p = [c for c in psx[p].callers
                    if c not in m_pd and psx[c].file and not psx[c].file.startswith("lib/")]
            if len(uc_d) == 1 and len(uc_p) == 1:
                changed |= add(uc_d[0], uc_p[0], "caller")
        # file contiguity: fill gaps between two matches in the same PSX file with equal gap size
        md = sorted(m_dp)
        for d0, d1 in zip(md, md[1:]):
            p0, p1 = psx[m_dp[d0]], psx[m_dp[d1]]
            i0, i1 = dc[d0].index, dc[d1].index
            if p0.file == p1.file and p1.index - p0.index == i1 - i0 > 1:
                for k in range(1, i1 - i0):
                    changed |= add(dcl[i0 + k].addr, by_file[p0.file][p0.index + k].key, "order")
        # extend from a match to its neighbours when the neighbour pair's callees agree
        for d, p in list(m_dp.items()):
            pf = psx[p]
            for step in (-1, 1):
                di, pi = dc[d].index + step, pf.index + step
                if 0 <= di < len(dcl) and 0 <= pi < len(by_file[pf.file]):
                    dn, pn = dcl[di], by_file[pf.file][pi]
                    if dn.addr in m_dp or pn.key in m_pd:
                        continue
                    dcal = set(c if isinstance(c, str) else m_dp.get(c) for c in d_callees(dn)) - {None}
                    pcal = set(p_callees(pn))
                    if dcal and dcal <= pcal and len(dcal) >= 2:
                        changed |= add(dn.addr, pn.key, "neighbour")

    # 3. consistency: within each PSX file, DC order must follow PSX order
    bad = 0
    for fl, fs in by_file.items():
        seq = [(m_pd[f.key], f.index) for f in fs if f.key in m_pd]
        seq.sort()
        for (_, a0), (_, a1) in zip(seq, seq[1:]):
            if a1 < a0:
                bad += 1

    # 4. runs of consecutive DC functions labelled with the same PSX file (unmatched ones are skipped)
    runs = []  # [file, first_idx, last_idx, matched]
    for d in dcl:
        p = m_dp.get(d.addr)
        if p is None:
            continue
        fl = psx[p].file
        if runs and runs[-1][0] == fl:
            runs[-1][2] = d.index
            runs[-1][3] += 1
        else:
            runs.append([fl, d.index, d.index, 1])
    # each file keeps its biggest run; other runs of that file are outliers (wrong or relocated matches)
    best = {}
    for r in runs:
        if r[3] > best.get(r[0], (None, 0))[1]:
            best[r[0]] = (id(r), r[3])
    keep = [r for r in runs if best[r[0]][0] == id(r)]
    outlier = set()
    for r in runs:
        if best[r[0]][0] != id(r):
            for i in range(r[1], r[2] + 1):
                if dcl[i].addr in m_dp and psx[m_dp[dcl[i].addr]].file == r[0]:
                    outlier.add(dcl[i].addr)

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "psx_match.csv"), "w", newline="\n") as f:
        f.write("dc_addr,dc_size,psx_file,psx_name,method,outlier\n")
        for d in dcl:
            p = m_dp.get(d.addr)
            f.write(f"{d.addr:08X},{d.end - d.addr:X},{psx[p].file if p else ''},"
                    f"{psx[p].name if p else ''},{method.get(d.addr, '')},{int(d.addr in outlier)}\n")

    # 5. split table: kept runs in DC order; unmatched DC functions between runs are reported as gaps
    lines = [f"# {len(m_dp)} of {len(game)} PSX game functions matched ({seeds} string seeds, "
             f"{len(outlier)} outliers, {bad} in-file order violations)",
             "# start/end: DC address range of the run's matched functions (end exclusive).",
             "# gap: unmatched DC functions after the run (file tail, DC-only code, or uncalled functions).",
             f"# {'start':>8} {'end':>8}  matched/psx  gap   file"]
    total_gap = 0
    for k, r in enumerate(keep):
        nxt = keep[k + 1][1] if k + 1 < len(keep) else len(dcl)
        gap = sum(1 for i in range(r[2] + 1, nxt) if dcl[i].addr not in m_dp or dcl[i].addr in outlier)
        total_gap += gap
        lines.append(f"  {dcl[r[1]].addr:08X} {dcl[r[2]].end:08X}  {r[3]:4d}/{len(by_file[r[0]]):<4d} "
                     f"{gap:4d}   {r[0]}")
    missing = sorted(set(by_file) - set(best))
    lines.append(f"# {total_gap} DC functions in gaps; PSX files with no match: {', '.join(missing) or 'none'}")
    with open(os.path.join(a.out, "psx_splits.txt"), "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("# methods:", dict(collections.Counter(method.values())))


if __name__ == "__main__":
    main()
