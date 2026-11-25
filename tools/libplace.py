#!/usr/bin/env python3
"""Decide which SDK library objects are linked where, so the build can link the real objects.

    libplace.py config/1st_read.toml

Reads [libraries] from the config (archives in preference order: when two archives hold the same object, the
first wins) and writes `[libraries] output` (config/lib_objects.txt):

    <addr> <size> <archive> <member> <section>      one line per placed section (NOBITS ones are in .bss)
    extern <addr> <name>                             symbols the libraries use but do not define (game code)

Method:
  1. Every section with contents is searched for in the ROM with relocated bytes masked (tools/libmatch.py).
     A section found at exactly one address anchors its object. Objects that define a global already defined by
     an accepted object are variants of the same code (libshinobi vs libprofiler...) and are skipped.
  2. Relocations (all R_SH_DIR32) then locate everything else: the original word at a relocation gives the
     address of the symbol it refers to. That places an object's other sections (.data, .bss, small
     sections libmatch cannot identify) and pulls in further objects that define referenced globals.
  3. Every placed section with contents is checked against the ROM.
"""
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from elfobj import ElfObject, read_archive  # noqa: E402
from libmatch import find_all  # noqa: E402

try:
    import tomllib
except ImportError:
    sys.exit("libplace.py needs Python 3.11+")

SHF_ALLOC = 2
SHT_NOBITS = 8
STB_LOCAL, STB_GLOBAL, STB_WEAK = 0, 1, 2
SHN_COMMON = 0xFFF2


class Obj:
    def __init__(self, archive, member, blob, pref):
        self.archive, self.member, self.pref = archive, member, pref
        self.elf = ElfObject(member, blob)
        self.secs = [i for i, s in enumerate(self.elf.sections) if s.flags & SHF_ALLOC and s.size > 0]
        self.defs = {}  # global name -> (section index, value)
        for name, val, _sz, info, shn in self.elf.symbols:
            if info >> 4 in (STB_GLOBAL, STB_WEAK) and 0 < shn < 0xFF00 and name:
                self.defs[name] = (shn, val)
        self.addr = {}  # section index -> address

    @property
    def key(self):
        return f"{self.archive}:{self.member}"


def load_objects(archives):
    objs = []
    for pref, path in enumerate(archives):
        base = os.path.basename(path)
        if path.lower().endswith(".a"):
            seen = {}
            for member, blob in read_archive(path):
                seen[member] = seen.get(member, 0) + 1
                name = member if seen[member] == 1 else f"{member}#{seen[member]}"
                try:
                    o = Obj(base, name, blob, pref)
                except ValueError:
                    continue
                # some SDK members declare section data past the end of the file; ld refuses them
                if any(s.type != SHT_NOBITS and len(s.data) < s.size for s in o.elf.sections):
                    continue
                objs.append(o)
        else:
            objs.append(Obj("", base, open(path, "rb").read(), pref))
    return objs


def solve(objs, anchors, rejected, rom, vram, excl):
    """Place objects (all sections or none). Returns (placed objects, externs, problems)."""
    rom_end = vram + len(rom)
    for o in objs:
        o.addr = {}

    def word(a):
        return struct.unpack_from("<I", rom, a - vram)[0]

    taken, defined, placed, problems = [], {}, [], []

    def overlaps(lo, hi):
        return any(lo < h and l < hi for l, h in taken)

    def accept(o):
        for n in o.defs:
            defined.setdefault(n, o)
        placed.append(o)

    def fits(o, si, a):
        sec = o.elf.sections[si]
        if sec.type == SHT_NOBITS:
            return True  # SHC's linker interleaves BSG with initialised data, so it may lie inside the file
        if not (vram <= a and a + sec.size <= rom_end) or any(lo <= a < hi for lo, hi in excl):
            return False
        m = o.elf.mask(sec)
        got = rom[a - vram:a - vram + sec.size]
        return all(not m[i] or got[i] == sec.data[i] for i in range(sec.size)) and not overlaps(a, a + sec.size)

    def put(o, si, a):
        sec = o.elf.sections[si]
        o.addr[si] = a
        if sec.type != SHT_NOBITS:
            taken.append((a, a + sec.size))

    # 1. anchors
    for _neg, _pref, a, o, si in anchors:
        if o.key in rejected or si in o.addr:
            continue
        sec = o.elf.sections[si]
        if overlaps(a, a + sec.size):
            continue
        if o not in placed:
            if any(n in defined and defined[n] is not o for n in o.defs):
                continue  # a variant of an object already accepted
            accept(o)
        put(o, si, a)

    # 2. relocations
    by_def = {}
    for o in objs:
        if o.key not in rejected:
            for n in o.defs:
                by_def.setdefault(n, o)
    externs = {}
    conflicts = set()
    changed = True
    while changed:
        changed = False
        for o in list(placed):
            for si, base in list(o.addr.items()):
                sec = o.elf.sections[si]
                if sec.type == SHT_NOBITS:
                    continue
                for off, rtype, symi, add in sec.relocs:
                    if rtype != 1:
                        problems.append(f"{o.key}:{sec.name}+{off:x}: relocation type {rtype}")
                        continue
                    inplace = struct.unpack_from("<I", sec.data, off)[0]
                    name, val, _sz, _info, shn = o.elf.symbols[symi]
                    tgt = (word(base + off) - add - inplace) & 0xFFFFFFFF
                    if 0 < shn < 0xFF00:
                        if shn not in o.addr:
                            a = (tgt - val) & 0xFFFFFFFF
                            if fits(o, shn, a) is not False:
                                put(o, shn, a)
                                changed = True
                            else:
                                problems.append(f"{o.key}:{o.elf.sections[shn].name}: reloc at {base + off:08X} "
                                                f"puts it at {a:08X}, which does not fit")
                        continue
                    if shn not in (0, SHN_COMMON):
                        continue
                    d = defined.get(name)
                    if d is None and name in by_def and not any(lo <= tgt < hi for lo, hi in excl):
                        c = by_def[name]
                        dsi, dval = c.defs[name]
                        a = (tgt - dval) & 0xFFFFFFFF
                        if not any(n in defined for n in c.defs) and fits(c, dsi, a) is not False:
                            accept(c)
                            put(c, dsi, a)
                            changed = True
                            continue
                    if d is None:
                        if externs.get(name, tgt) != tgt:
                            problems.append(f"extern {name}: {externs[name]:08X} vs {tgt:08X}")
                        externs[name] = tgt
                        continue
                    dsi, dval = d.defs[name]
                    a = (tgt - dval) & 0xFFFFFFFF
                    if dsi in d.addr:
                        if d.addr[dsi] != a:
                            problems.append(f"{name}: {o.key} expects {a:08X}, {d.key} is at {d.addr[dsi]:08X}")
                            conflicts.add(o.key)
                    elif fits(d, dsi, a) is not False:
                        put(d, dsi, a)
                        changed = True
        # sections nothing points at: a unique non-overlapping search hit
        if not changed:
            for o in placed:
                for si in o.secs:
                    if si in o.addr or o.elf.sections[si].type == SHT_NOBITS:
                        continue
                    hs = [h for h in o.hits.get(si, []) if fits(o, si, h)]
                    if len(hs) == 1:
                        put(o, si, hs[0])
                        changed = True
    externs = {n: a for n, a in externs.items() if n not in defined}
    return placed, externs, problems, conflicts


def main():
    cfg_path = sys.argv[1]
    with open(cfg_path, "rb") as f:
        cfg = tomllib.load(f)
    b, lc = cfg["binary"], cfg["libraries"]
    rom = open(b["rom"], "rb").read()
    vram = b["vram"]
    rom_end = vram + len(rom)
    archives = []
    for pat in lc["archives"]:
        hits = sorted(glob.glob(os.path.expanduser(pat)))
        if not hits:
            sys.exit(f"[libraries] {pat}: no such file")
        archives += hits
    objs = load_objects(archives)
    excl = [(int(a, 0), int(z, 0)) for a, z in lc.get("exclude", [])]

    anchors = []
    for o in objs:
        for si in o.secs:
            sec = o.elf.sections[si]
            if sec.type == SHT_NOBITS:
                continue
            hits = find_all(rom, sec.data, o.elf.mask(sec), max(1, min(sec.align or 1, 4)))
            o.hits = getattr(o, "hits", {})
            o.hits[si] = [h + vram for h in hits or [] if not any(lo <= h + vram < hi for lo, hi in excl)]
            if sec.size >= lc.get("min_size", 16) and len(o.hits[si]) == 1:
                anchors.append((-sec.size, o.pref, o.hits[si][0], o, si))
    anchors.sort(key=lambda c: (c[0], c[1], c[2]))

    rejected, blobs = set(), []
    while True:
        placed, externs, problems, conflicts = solve(objs, anchors, rejected, rom, vram, excl)
        bad = [o for o in placed if any(si not in o.addr for si in o.secs) or o.key in conflicts]
        if not bad:
            break
        for o in bad:
            miss = [o.elf.sections[si].name for si in o.secs if si not in o.addr]
            why = f"no address for {', '.join(miss)}" if miss else "a symbol it uses is linked elsewhere"
            blobs.append(f"{o.key}: left as a blob ({why})")
            rejected.add(o.key)
    problems = blobs + problems

    # ---- 3. report -------------------------------------------------------------------------------------------
    rows = []
    for o in placed:
        for si in o.secs:
            s = o.elf.sections[si]
            rows.append((o.addr[si], s.size, o.archive or "-", o.member, s.name))
    rows.sort()
    out = lc["output"]
    with open(out, "w", newline="\n") as f:
        f.write("# SDK library sections and where they are linked. Generated by tools/libplace.py.\n")
        f.write("# addr size archive member section\n")
        for a, size, arc, mem, sec in rows:
            f.write(f"{a:08X} {size:6X} {arc} {mem} {sec}\n")
        for name, a in sorted(externs.items(), key=lambda x: x[1]):
            f.write(f"extern {a:08X} {name}\n")
    nobj = len({(r[2], r[3]) for r in rows})
    text = sum(r[1] for r in rows if r[0] < rom_end)
    print(f"{out}: {nobj} objects, {len(rows)} sections ({text:#x} bytes in the ROM), {len(externs)} externs")
    for p in dict.fromkeys(problems):
        print("  note:", p)


if __name__ == "__main__":
    main()


# ---- used by split.py / disasm.py ---------------------------------------------------------------------------
def archive_paths(cfg):
    """archive basename ("-" for a loose .obj: then the member name) -> path."""
    out = {}
    for pat in cfg["libraries"]["archives"]:
        for p in sorted(glob.glob(os.path.expanduser(pat))):
            out.setdefault(os.path.basename(p), p)
    return out


def read_placements(path):
    """-> (rows [(addr, size, archive, member, section)], externs {asm name: addr})."""
    rows, externs = [], {}
    if os.path.exists(path):
        for line in open(path):
            p = line.split()
            if not p or p[0].startswith("#"):
                continue
            if p[0] == "extern":
                externs[p[2]] = int(p[1], 16)
            else:
                rows.append((int(p[0], 16), int(p[1], 16), p[2], p[3], p[4]))
    return rows, externs


def uncommon(blob):
    """Turn COMMON symbols into undefined references, so the linker script's PROVIDE puts them at their original
    address instead of ld allocating them (there is no *(COMMON) placement)."""
    elf = ElfObject("", blob)
    out = bytearray(blob)
    (shoff,) = struct.unpack_from("<I", blob, 0x20)
    shentsize, shnum = struct.unpack_from("<HH", blob, 0x2E)
    for i in range(shnum):
        h = struct.unpack_from("<IIIIIIIIII", blob, shoff + i * shentsize)
        if h[1] != 2:  # SHT_SYMTAB
            continue
        for off in range(h[4], h[4] + h[5], 16):
            if struct.unpack_from("<H", blob, off + 14)[0] == SHN_COMMON:
                struct.pack_into("<IIBBH", out, off + 4, 0, 0, blob[off + 12], 0, 0)
    del elf
    return bytes(out)


def member_blob(paths, archive, member):
    if archive == "-":
        return open(paths[member], "rb").read()
    want, n = member.split("#")[0], int(member.split("#")[1]) if "#" in member else 1
    for name, blob in read_archive(paths[archive]):
        if name == want:
            n -= 1
            if n == 0:
                return blob
    raise KeyError(f"{archive}:{member}")


def placed_objects(cfg):
    """Yield (archive, member, blob, {section name: addr}) for every placed object."""
    rows, _ = read_placements(cfg["libraries"]["output"])
    paths = archive_paths(cfg)
    by_obj = {}
    for a, _size, arc, mem, sec in rows:
        by_obj.setdefault((arc, mem), {})[sec] = a
    cache = {}
    for (arc, mem), secs in by_obj.items():
        if arc not in cache and arc != "-":
            cache[arc] = dict(_members(paths[arc]))
        blob = open(paths[mem], "rb").read() if arc == "-" else cache[arc][mem]
        yield arc, mem, blob, secs


def _members(path):
    seen = {}
    for name, blob in read_archive(path):
        seen[name] = seen.get(name, 0) + 1
        yield (name if seen[name] == 1 else f"{name}#{seen[name]}"), blob


def library_symbols(cfg):
    """{addr: (asm name, size)} for the global symbols of the placed objects, plus externs (size 0)."""
    out = {}
    for _arc, mem, blob, secs in placed_objects(cfg):
        elf = ElfObject(mem, blob)
        per_sec = {}
        for name, val, _sz, info, shn in elf.symbols:
            if info >> 4 in (STB_GLOBAL, STB_WEAK) and 0 < shn < 0xFF00 and name:
                sname = elf.sections[shn].name
                if sname in secs:
                    per_sec.setdefault(shn, []).append((val, name))
        for shn, lst in per_sec.items():
            lst.sort()
            base, end = secs[elf.sections[shn].name], elf.sections[shn].size
            for i, (val, name) in enumerate(lst):
                nxt = lst[i + 1][0] if i + 1 < len(lst) else end
                out.setdefault(base + val, (name, max(0, nxt - val)))
    _, externs = read_placements(cfg["libraries"]["output"])
    for name, a in externs.items():
        out.setdefault(a, (name, 0))
    return out
