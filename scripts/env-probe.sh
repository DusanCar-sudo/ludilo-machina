#!/data/data/com.termux/files/usr/bin/sh
echo "prefix=${PREFIX:-none}"; uname -m
command -v aapt2 d8 apksigner zipalign ecj java 2>/dev/null
free -m 2>/dev/null | sed -n 2p; df -h "${HOME:-.}" | tail -1
