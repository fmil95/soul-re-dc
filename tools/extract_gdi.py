#!/usr/bin/env python3
"""Extract files from a Dreamcast GD-ROM image (.gdi + raw 2352-byte tracks).

Usage:
    extract_gdi.py <disc.gdi> --list
    extract_gdi.py <disc.gdi> <outdir> [FILE ...]   (default: 1ST_READ.BIN)

IP.BIN (the first 16 sectors of the high-density area) is always written too.
"""
import argparse
import os
import struct
import sys

SECTOR = 2352
USER_OFS = 16  # mode 1 sync+header
USER_SIZE = 2048


class GDI:
    def __init__(self, gdi_path):
        base = os.path.dirname(os.path.abspath(gdi_path))
        with open(gdi_path) as f:
            lines = [l.split() for l in f.read().splitlines() if l.strip()]
        self.tracks = []
        for t in lines[1:]:
            num, lba, ttype, ssize, name = int(t[0]), int(t[1]), int(t[2]), int(t[3]), t[4].strip('"')
            if ttype != 4:
                continue  # audio
            assert ssize == SECTOR, f"unsupported sector size {ssize}"
            self.tracks.append((lba, open(os.path.join(base, name), "rb")))
        self.tracks.sort(key=lambda t: -t[0])
        # High-density data area starts at the first data track at/after LBA 45000.
        self.hd_start = min(l for l, _ in self.tracks if l >= 45000)

    def read(self, lba, count=1):
        out = bytearray()
        for i in range(count):
            for start, fh in self.tracks:
                if lba + i >= start:
                    break
            else:
                raise ValueError(f"LBA {lba + i} not in any data track")
            fh.seek((lba + i - start) * SECTOR + USER_OFS)
            out += fh.read(USER_SIZE)
        return bytes(out)

    def files(self):
        pvd = self.read(self.hd_start + 16)
        assert pvd[1:6] == b"CD001", "no ISO9660 PVD found"
        root = pvd[156:156 + 34]
        out = []
        self._walk(struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0], "", out)
        return out

    def _walk(self, lba, size, path, out):
        data = self.read(lba, (size + USER_SIZE - 1) // USER_SIZE)
        i = 0
        while i < size:
            ln = data[i]
            if ln == 0:
                i = (i // USER_SIZE + 1) * USER_SIZE
                continue
            rec = data[i:i + ln]
            i += ln
            elba = struct.unpack_from("<I", rec, 2)[0]
            esz = struct.unpack_from("<I", rec, 10)[0]
            flags, nl = rec[25], rec[32]
            name = rec[33:33 + nl]
            if name in (b"\x00", b"\x01"):
                continue
            p = path + "/" + name.decode("latin1").split(";")[0]
            if flags & 2:
                self._walk(elba, esz, p, out)
            else:
                out.append((p, elba, esz))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gdi")
    ap.add_argument("outdir", nargs="?")
    ap.add_argument("names", nargs="*")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    disc = GDI(a.gdi)
    entries = disc.files()
    if a.list or not a.outdir:
        for p, lba, size in entries:
            print(f"{size:>12} {lba:>8} {p}")
        return
    os.makedirs(a.outdir, exist_ok=True)
    with open(os.path.join(a.outdir, "IP.BIN"), "wb") as f:
        f.write(disc.read(disc.hd_start, 16))
    wanted = {n.upper() for n in (a.names or ["1ST_READ.BIN"])}
    for p, lba, size in entries:
        if p.split("/")[-1].upper() in wanted:
            dst = os.path.join(a.outdir, p.split("/")[-1])
            with open(dst, "wb") as f:
                f.write(disc.read(lba, (size + USER_SIZE - 1) // USER_SIZE)[:size])
            print(f"wrote {dst} ({size} bytes)")


if __name__ == "__main__":
    sys.exit(main())
