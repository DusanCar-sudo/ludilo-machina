#!/data/data/com.termux/files/usr/bin/sh
# Make `ludilo` a global command (works from any directory). Run from the repo root.
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${PREFIX:-$HOME/.local}/bin"
mkdir -p "$BIN"
cat > "$BIN/ludilo" <<EOS
#!/bin/sh
PYTHONPATH="$REPO\${PYTHONPATH:+:\$PYTHONPATH}" exec python3 -m ludilo "\$@"
EOS
chmod +x "$BIN/ludilo"
echo "installed: $BIN/ludilo -> $REPO"
