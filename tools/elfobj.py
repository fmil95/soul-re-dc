"""Minimal ELF32 (SH, little-endian) relocatable object + ar archive reader. No dependencies."""
import struct

# SH relocation type -> number of bytes the relocation patches (0 = relaxation marker only)
SH_RELOC_SIZE = {
    0: 0,   # R_SH_NONE
    1: 4,   # R_SH_DIR32
    2: 4,   # R_SH_REL32
    3: 2,   # R_SH_DIR8WPN
    4: 2,   # R_SH_IND12W
    5: 2,   # R_SH_DIR8WPL
    6: 2,   # R_SH_DIR8WPZ
    7: 2,   # R_SH_DIR8BP
    8: 2,   # R_SH_DIR8W
    9: 2,   # R_SH_DIR8L
    25: 2,  # R_SH_SWITCH16
    26: 4,  # R_SH_SWITCH32
    27: 0, 28: 0, 29: 0, 30: 0, 31: 0, 32: 0,  # USES/COUNT/ALIGN/CODE/DATA/LABEL
    33: 2,  # R_SH_SWITCH8
    34: 0, 35: 0,  # GNU_VTINHERIT / VTENTRY
}

SHT_SYMTAB, SHT_RELA, SHT_NOBITS, SHT_REL = 2, 4, 8, 9


class Section:
    def __init__(self, name, sh_type, flags, addralign, data, size):
        self.name, self.type, self.flags, self.align = name, sh_type, flags, addralign
        self.data, self.size = data, size
        self.relocs = []  # (offset, type, symbol_index, addend)


class ElfObject:
    def __init__(self, name, blob):
        self.name = name
        if blob[:4] != b"\x7fELF":
            raise ValueError(f"{name}: not ELF")
        if blob[4] != 1 or blob[5] != 1:
            raise ValueError(f"{name}: not ELF32 little-endian")
        (e_shoff,) = struct.unpack_from("<I", blob, 0x20)
        e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", blob, 0x2E)
        hdrs = [struct.unpack_from("<IIIIIIIIII", blob, e_shoff + i * e_shentsize) for i in range(e_shnum)]
        shstr = hdrs[e_shstrndx]
        strtab = blob[shstr[4]:shstr[4] + shstr[5]]

        def cstr(tab, off):
            return tab[off:tab.index(b"\0", off)].decode("latin1")

        self.sections = []
        for h in hdrs:
            name_off, sh_type, flags, _addr, off, size, link, info, align, entsize = h
            data = b"" if sh_type == SHT_NOBITS else blob[off:off + size]
            s = Section(cstr(strtab, name_off), sh_type, flags, align, data, size)
            s.link, s.info = link, info
            self.sections.append(s)

        self.symbols = []  # (name, value, size, info, shndx)
        for s in self.sections:
            if s.type == SHT_SYMTAB:
                strs = self.sections[s.link].data
                for i in range(0, len(s.data), 16):
                    nm, val, sz, inf, _oth, shn = struct.unpack_from("<IIIBBH", s.data, i)
                    self.symbols.append((cstr(strs, nm), val, sz, inf, shn))
        for s in self.sections:
            if s.type in (SHT_RELA, SHT_REL):
                tgt = self.sections[s.info]
                step = 12 if s.type == SHT_RELA else 8
                for i in range(0, len(s.data), step):
                    off, info = struct.unpack_from("<II", s.data, i)
                    add = struct.unpack_from("<i", s.data, i + 8)[0] if step == 12 else 0
                    tgt.relocs.append((off, info & 0xFF, info >> 8, add))

    def mask(self, sec):
        """Return a bytearray, same length as sec.data, with 1 where bytes are fixed and 0 where relocated."""
        m = bytearray(b"\x01" * len(sec.data))
        for off, rtype, _sym, _add in sec.relocs:
            n = SH_RELOC_SIZE.get(rtype, 4)
            for k in range(off, min(off + n, len(m))):
                m[k] = 0
        return m


def read_archive(path):
    """Yield (member_name, bytes) for each member of a SysV/GNU ar archive."""
    with open(path, "rb") as f:
        blob = f.read()
    if blob[:8] != b"!<arch>\n":
        raise ValueError(f"{path}: not an ar archive")
    pos, longnames = 8, b""
    while pos + 60 <= len(blob):
        hdr = blob[pos:pos + 60]
        name = hdr[:16].decode("latin1").rstrip()
        size = int(hdr[48:58].decode().strip())
        data = blob[pos + 60:pos + 60 + size]
        pos += 60 + size + (size & 1)
        if name == "//":
            longnames = data
            continue
        if name in ("/", "/SYM64/", "__.SYMDEF", "__.SYMDEF SORTED"):
            continue
        if name.startswith("/") and name[1:].isdigit():
            o = int(name[1:])
            end = longnames.find(b"/\n", o)
            if end < 0:
                end = longnames.find(b"\n", o)
            name = longnames[o:end].decode("latin1")
        yield name.rstrip("/"), data
