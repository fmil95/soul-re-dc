#!/bin/bash
# Download the objdiff CLI (pinned) to ~/.local/share/soul-re-dc/bin. objdiff.json is written by tools/split.py.
# GUI: https://github.com/encounter/objdiff/releases (open this repo's root as the project directory).
set -e
VER="${OBJDIFF_VERSION:-v3.8.3}"
D="$HOME/.local/share/soul-re-dc/bin"
mkdir -p "$D"
case "$(uname -m)" in
  x86_64) arch=x86_64 ;;
  aarch64) arch=aarch64 ;;
  *) echo "unsupported arch $(uname -m)" >&2; exit 1 ;;
esac
curl -fL -o "$D/objdiff-cli" "https://github.com/encounter/objdiff/releases/download/$VER/objdiff-cli-linux-$arch"
chmod +x "$D/objdiff-cli"
"$D/objdiff-cli" --version
