#!/bin/bash
# Run a KATANA SDK GNU tool under Wine: tools/dctool.sh <gcc|cc1|cpp|as|ld|objdump|objcopy|nm|ar> args...
# Paths are passed through unchanged; use relative paths (run from the repo root).
set -e
T="${SRDC_TOOLCHAIN:-$HOME/.local/share/soul-re-dc/gnu}"
tool="$1"; shift
case "$tool" in
  cc1|cpp|cc1plus) exe="$T/lib/gcc-lib/sh-elf/2.9-SYSDEV-sh4p2_final-991007/$tool.exe" ;;
  *)               exe="$T/Bin/$tool.exe" ;;
esac
[ -f "$exe" ] || { echo "dctool: $exe not found (run tools/setup_toolchain.sh)" >&2; exit 127; }
export WINEDEBUG=-all
exec wine "$exe" "$@" </dev/null
