# soul-re-dc

Matching decompilation of **Legacy of Kain: Soul Reaver** for the Sega Dreamcast
(NTSC-U v1.000, product T36802N, IP.BIN date 1999-12-20).

| File | SHA-1 |
|---|---|
| `1ST_READ.BIN` | `92b051a490599e062a19b5cbc4ecab83f26428f3` |

## Status

The game code builds from C in Ship-of-Theseus style:

- 116 source files (83 carried over from PSX, 33 DC-only) with 3474 functions. Every function not yet
  decompiled is pulled in with `INCLUDE_ASM`.
- The output is byte-identical.
- 2 functions are decompiled (`CAMERA_Lock`, `CAMERA_Unlock`).

## Decompiling

1. Pick a function in `src/<file>.c`. Its asm is in `asm/nonmatchings/<file>/<name>.s`, and the PSX C is in
   soul-re under the same file name.
2. Replace its `INCLUDE_ASM(...)` line with the C definition.
3. Run `make`. It must still print `OK`; `tools/compare.py` reports the first differing address otherwise.

Things to know:

- **Compiler flags:** `-ml -m4-single-only -O2 -fno-delayed-branch`. Branch delay slots are left as `nop`
  (3618 of 3631 `rts` in the game), and the frame pointer is kept (`mov r15,r14`), as plain `-O2` does in this GCC.
- **Headers:** every `src/<file>.c` includes its own `include/<file>.h`. These headers come from soul-re
  (`tools/import_psx_headers.py`, imported from commit `45b43285`), and the overlay headers moved to their DC
  location (for example `Overlays/aluka/aluka.h` became `Game/MONSTER/ALUKA.h`). All structs come from
  `include/Game/TYPES.h` and `EXTRA.h`. DC-only files get a minimal header that only includes `common.h`.
  - `include/common.h` is a DC version of soul-re's:
    - Varargs come from the compiler's `<stdarg.h>`, because the SH ABI passes them in registers.
    - The MIPS GTE macros (`Libs/GTE.h`) are left out.
  - The struct layout appears to be unchanged from PSX: `CAMERA_Lock` matches using the PSX `Camera` struct
    (`lock` at `0xEC`).
  - DC-specific edits so far: `MEMPACK.h` and `TIMER.h` now include `common.h` themselves.
- **Data:** `.rodata`/`.data` are still one blob. A decompiled function that needs its own string literals or
  static data can't match until that data is split out of the blob.
- **Symbols:** asm refers to data as `D_<ADDR>` and to SDK functions by name. These are defined in the generated
  linker script, so C can use them as `extern`.

### How the files were made

- `tools/gen_functions.py` writes `config/functions.csv`, which is the function → file → name table. Edit it
  by hand to rename or re-split. Notes:
  - **File boundaries:** `ld` pads between object files with zeros, while gas pads between functions with
    `nop`s. A zero-padded function start therefore begins a new file. This gives 96 boundaries, which agree
    with the PSX-derived order.
  - **Function names:** PSX names come from `config/psx_match.csv`. Unmatched functions are `func_<ADDR>`, and
    DC-only files are `src/dc/unk_<ADDR>.c`. The PSX monster overlays become `src/Game/MONSTER/<NAME>.c`.
- `tools/gen_c.py` (`make gen-c`) creates any missing `src/**/*.c`, each including its own header, and
  creates missing headers. It never overwrites existing files.
- The build compiles through the `gcc` driver (`gcc -S`, then `as`) rather than calling `cpp`/`cc1` directly.
  That way the predefines (`__GNUC__`, …) and the compiler's system headers match the original build.
- `tools/gen_asm.py` runs from `make split` and writes one `.s` per function:
  - instructions as `.word` with the SDK `objdump` text in comments
  - literal-pool addresses as `.long <symbol>`
  - a leading `.align 5`, with trailing padding dropped so that gas and `ld` regenerate it

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

### Cross-reference with the PSX decomp

`make psx-match PSX=~/soul-re` matches DC functions to PSX functions using the
[soul-re](https://github.com/fmil95/soul-re) build (`build/*.elf`, `build/*.map`) and writes:

- `config/psx_match.csv`: every DC function start, with the PSX name and file where matched.
- `config/psx_splits.txt`: DC address range per PSX file.

How it matches:

- **DC function starts (3096):** every 32-byte-aligned word in the binary that points into game code.
  GCC calls through literal pools, and functions are `.align 5`.
- **Seeds:** functions with identical sets of string references on both platforms.
- **Propagation:** callee lists (PSX `jal` targets vs DC literal-pool call targets, with libc calls named on
  both sides), unique unmatched callers, and source order within a file.

Current result: 2264 of 2694 PSX functions are matched.

DC link order:

1. `Game/*.c`, in nearly alphabetical order.
2. The platform directory (`SUPPORT`, `AADLIB`, `AADSEQEV`, `AADSFX`, `MAIN`), which replaces `PSX/`.
3. `RAZIEL/`, `LOCAL/`, `MENU/`, `G2/`, `PLAN/`.
4. `MONSTER/`, with the PSX overlays (`aluka`, `kain`, `walboss`, …) linked into it in alphabetical order.
5. DC rewrites of `LOAD3D`, `STRMLOAD`, `CINEMA` and `DRAW`. These match PSX poorly; the remaining DC-only code
   sits around them.

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
- In SH gas, `.long` aligns itself to 4 bytes. That's why the generated asm uses `.word` for everything
  except literal-pool words, which are always 4-byte aligned.

## Layout

```
config/1st_read.toml   segment map (the source of truth for splitting and linking)
tools/extract_gdi.py   GD-ROM (.gdi) file extractor
tools/split.py         config -> build/bin/*.o blobs + build/1st_read.ld
tools/libmatch.py      locate SDK library objects in the binary (relocation-masked byte match)
tools/elfobj.py        tiny ELF/ar reader used by libmatch
tools/compare.py       SHA-1 check + per-segment diff report
tools/psx_match.py     match DC functions to the PSX decomp (soul-re), derive file splits
tools/gen_functions.py config/psx_match.csv -> config/functions.csv (file splits + names)
tools/gen_c.py         create src/**/*.c INCLUDE_ASM stubs
tools/gen_asm.py       asm/nonmatchings/**/*.s (run by split.py)
tools/dctool.sh        run SDK tools under Wine
config/functions.csv   function table: address, file, name (hand-editable)
src/                   game C sources (INCLUDE_ASM + decompiled functions)
include/               headers imported from soul-re (Game/**, Libs/SDK.h) + DC common.h, include_asm.h
tools/import_psx_headers.py  copy soul-re headers into include/ (overlays mapped to DC paths)
asm/nonmatchings/      generated, not committed
```

## Next steps

1. Split `.rodata`/`.data` per file, so functions with string literals and static data can match.
2. Set up objdiff for per-function diffing, and a progress report.
3. Replace the `sdk_shc` and `lib_text` blobs with the real SDK library objects.
