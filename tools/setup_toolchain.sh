#!/bin/bash
# Install the KATANA SDK GNU toolchain (gcc 2.9-SYSDEV-sh4p2_final-991007) where Wine can run it.
#
# Why this is needed:
#  * The toolchain is Cygwin B20 era. Its cygwin1.dll crashes during DllMain when Wine maps it from a
#    WSL /mnt/<drive> (drvfs) path, so it must live on a native Linux filesystem.
#  * cc1/cpp/as/ld are spawned from different directories, so each needs cygwin1.dll next to it.
#
# Usage: tools/setup_toolchain.sh [KATANA dir] [install dir]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KATANA="${1:-$ROOT/KATANA}"
DEST="${2:-${SRDC_TOOLCHAIN:-$HOME/.local/share/soul-re-dc/gnu}}"
SRC="$KATANA/Utl/Dev/Gnu"

[ -f "$SRC/Bin/gcc.exe" ] || { echo "error: $SRC/Bin/gcc.exe not found" >&2; exit 1; }
command -v wine >/dev/null || { echo "error: wine is not installed" >&2; exit 1; }

case "$DEST" in
  /mnt/*) echo "error: install dir must not be on a /mnt drive (cygwin1.dll crashes there)" >&2; exit 1;;
esac

echo "installing $SRC -> $DEST"
rm -rf "$DEST"
mkdir -p "$(dirname "$DEST")"
cp -r "$SRC" "$DEST"

GCCLIB="$DEST/lib/gcc-lib/sh-elf/2.9-SYSDEV-sh4p2_final-991007"
cp "$DEST/Bin/cygwin1.dll" "$GCCLIB/"
cp "$DEST/Bin/cygwin1.dll" "$DEST/sh-elf/bin/"

export WINEDEBUG=-all
ver="$(wine "$DEST/Bin/gcc.exe" --version </dev/null 2>/dev/null | tr -d '\r')"
echo "gcc --version: $ver"
[ "$ver" = "2.9-SYSDEV-sh4p2_final-991007" ] || { echo "error: unexpected gcc version" >&2; exit 1; }
echo "ok. export SRDC_TOOLCHAIN=$DEST  (this is the default, so only needed if you changed it)"
