# soul-re-dc

Matching decompilation of **Legacy of Kain: Soul Reaver** for the Sega Dreamcast
(NTSC-U v1.000, product T36802N, IP.BIN date 1999-12-20).

| File | SHA-1 |
|---|---|
| `1ST_READ.BIN` | `92b051a490599e062a19b5cbc4ecab83f26428f3` |

## Status

Toolchain runs, and the binary rebuilds byte-identical from blobs. Nothing is decompiled yet.

## What we know

- **Compiler:** the game code is built with the KATANA SDK's GNU toolchain, **gcc `2.9-SYSDEV-sh4p2_final-991007`**
  (Cygnus SH4 phase 2, with Sega SOA patches) and binutils `2.9-sh4-980812`. Hitachi SHC was not used.
  Evidence: about 1000 GCC-style ascending register-save prologues (`mov.l r8,@-r15; mov.l r9,@-r15 …`) in the
  game code. The SHC-built SDK libraries have none and use descending saves (`r14, r13, …`) instead.
- **Compiler source:** the SYSDEV sources were only ever available on request from Sega DTS. So we run the
  original binaries under Wine rather than rebuilding the compiler.
- **SDK libraries:** these are the exact builds shipped in the KATANA SDK (Shinobi 1.43, Kamui2 16.3.2.4,
  Sofdec 2.19, ADXF 5.53, …). `tools/libmatch.py` locates their objects in the binary. They don't need
  decompiling and can eventually be linked straight from `KATANA/Lib/Gnu/*.a`.

### Memory map (`1ST_READ.BIN` is loaded at `0x8C010000`)

| Range | Contents |
|---|---|
| `8C010000`–`8C05AC20` | SHC-built SDK libraries (Shinobi `PSG`/`CSG`/`DSG` sections) and `strt1`/`strt2` |
| `8C05AC20`–`8C12A9E0` | **Game `.text`** (GCC), about 832 KB |
| `8C12A9E0`–`8C138100` | GCC-side libraries: audio64, sh4nlfzz, shinobi (GNU parts), libc, libgcc |
| `8C138100`–`8C35BB64` | `.rodata` and `.data`. `.bss` is not stored in the file. |

## Setup

Building happens in **WSL/Linux with Wine** (tested: Ubuntu 24.04, wine 9.0).

1. Put the GDI set (`*.gdi`, `track*.bin`, `track*.raw`) in the repo root.
2. Put the KATANA SDK in `KATANA/` (it must contain `Utl/Dev/Gnu`).
3. Run:
   ```sh
   make setup   # extracts rom/1ST_READ.BIN and installs the toolchain to ~/.local/share/soul-re-dc/gnu
   make         # builds build/1ST_READ.BIN and checks its SHA-1
   ```

These inputs are gitignored and must never be committed.

### Toolchain notes

- The Cygwin B20 `cygwin1.dll` shipped with the SDK crashes during `DllMain` on Windows 11. Under Wine it also
  crashes when loaded from a WSL `/mnt/c` path. `tools/setup_toolchain.sh` therefore copies the toolchain to
  the Linux filesystem and places `cygwin1.dll` next to `cc1`, `cpp`, `as` and `ld`.
- `tools/dctool.sh <tool> args…` runs any SDK tool under Wine (for example `gcc`, `cc1`, `cpp`, `as`, `ld`,
  `objdump`, `objcopy`).
- binutils 2.9 has no `.incbin`, so `tools/bin2elf.py` wraps raw blobs in ELF objects.
- The default compile flags are `-ml -m4-single-only -O2`. These are not verified per file yet: some game
  functions keep a frame pointer (`mov r15,r14`), so flags may vary.

## Layout

```
config/1st_read.toml   segment map (the source of truth for splitting and linking)
tools/extract_gdi.py   GD-ROM (.gdi) file extractor
tools/split.py         config -> build/bin/*.o blobs + build/1st_read.ld
tools/libmatch.py      locate SDK library objects in the binary (relocation-masked byte match)
tools/elfobj.py        tiny ELF/ar reader used by libmatch
tools/compare.py       SHA-1 check + per-segment diff report
tools/dctool.sh        run SDK tools under Wine
src/  include/  asm/   (to come)
```

## Next steps

1. A disassembler/splitter that turns `game_text` into one GAS-syntax `.s` per function, with symbols and
   literal pools, that reassembles byte-identically with the SDK `as`.
2. Replace the `sdk_shc` and `lib_text` blobs with the real SDK library objects.
3. Set up objdiff for per-function diffing, then start matching C, reusing the PS1 decomp's sources where they apply.
