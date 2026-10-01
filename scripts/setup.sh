#!/data/data/com.termux/files/usr/bin/sh
# Install the on-device Android toolchain (package names verified on Termux aarch64; no zipalign pkg exists, apk.py aligns itself).
set -e
pkg update -y
for p in python openjdk-17 aapt2 apksigner d8 ecj android-tools termux-api curl; do
  pkg install -y "$p" || echo "MISSING PACKAGE: $p"
done
sh "$(dirname "$0")/install.sh"
mkdir -p ~/.ludilo
[ -f ~/.ludilo/android.jar ] || curl -fL -o ~/.ludilo/android.jar \
  https://github.com/Sable/android-platforms/raw/master/android-33/android.jar || echo "android.jar download failed: place one at ~/.ludilo/android.jar"
echo "Then: ludilo config   and   ludilo"
