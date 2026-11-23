#!/usr/bin/env python3
"""Wrap a raw binary blob in an ELF32 SH little-endian relocatable object.

Usage: bin2elf.py <in.bin> <out.o> [--section .text] [--symbol name] [--align 4]

The 1998 SDK binutils (2.9) has neither `.incbin` nor `objcopy -B`, so blobs are converted here.
"""
import argparse
import struct

EM_SH = 42
SHT_PROGBITS, SHT_SYMTAB, SHT_STRTAB = 1, 2, 3
SHF_WRITE, SHF_ALLOC, SHF_EXEC = 1, 2, 4


def flags_for(name):
    if name.startswith(".text") or name.startswith("P"):
        return SHF_ALLOC | SHF_EXEC
    if name.startswith(".rodata") or name.startswith("C"):
        return SHF_ALLOC
    return SHF_ALLOC | SHF_WRITE


def build(data, secname, symbol, align):
    shstr = b"\0" + secname.encode() + b"\0.symtab\0.strtab\0.shstrtab\0"
    n_sec = 1
    n_symtab = shstr.index(b".symtab")
    n_strtab = shstr.index(b".strtab")
    n_shstr = shstr.index(b".shstrtab")
    strtab = b"\0"
    syms = [struct.pack("<IIIBBH", 0, 0, 0, 0, 0, 0)]
    syms.append(struct.pack("<IIIBBH", 0, 0, 0, 3, 0, 1))  # STT_SECTION, local
    first_global = len(syms)
    if symbol:
        strtab += symbol.encode() + b"\0"
        syms.append(struct.pack("<IIIBBH", 1, 0, len(data), (1 << 4) | 0, 0, 1))  # GLOBAL NOTYPE
        strtab += (symbol + "_end").encode() + b"\0"
        syms.append(struct.pack("<IIIBBH", len(symbol) + 2, len(data), 0, (1 << 4) | 0, 0, 1))
    symtab = b"".join(syms)

    body = bytearray(b"\0" * 52)
    def put(blob, al=4):
        while len(body) % al:
            body.append(0)
        off = len(body)
        body.extend(blob)
        return off
    o_data = put(data, max(4, align))
    o_sym = put(symtab)
    o_str = put(strtab, 1)
    o_shs = put(shstr, 1)
    while len(body) % 4:
        body.append(0)
    shoff = len(body)

    def sh(name, typ, flags, off, size, link=0, info=0, al=1, ent=0):
        return struct.pack("<IIIIIIIIII", name, typ, flags, 0, off, size, link, info, al, ent)
    shdrs = [
        sh(0, 0, 0, 0, 0),
        sh(n_sec, SHT_PROGBITS, flags_for(secname), o_data, len(data), al=align),
        sh(n_symtab, SHT_SYMTAB, 0, o_sym, len(symtab), link=3, info=first_global, al=4, ent=16),
        sh(n_strtab, SHT_STRTAB, 0, o_str, len(strtab)),
        sh(n_shstr, SHT_STRTAB, 0, o_shs, len(shstr)),
    ]
    body.extend(b"".join(shdrs))
    ehdr = struct.pack("<16sHHIIIIIHHHHHH", b"\x7fELF\x01\x01\x01" + b"\0" * 9, 1, EM_SH, 1, 0, 0, shoff,
                       0, 52, 0, 0, 40, len(shdrs), 4)
    body[:52] = ehdr
    return bytes(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--section", default=".data")
    ap.add_argument("--symbol")
    ap.add_argument("--align", type=int, default=4)
    a = ap.parse_args()
    with open(a.src, "rb") as f:
        data = f.read()
    with open(a.dst, "wb") as f:
        f.write(build(data, a.section, a.symbol, a.align))


if __name__ == "__main__":
    main()
