#!/data/data/com.termux/files/usr/bin/sh
# Install the on-device Android toolchain. UNVERIFIED on a real phone: package names may differ.
set -e
pkg update -y
pkg install -y python openjdk-17 aapt2 apksigner d8 ecj android-tools termux-api zipalign || \
  echo "some packages missing: install them individually and tell the agent which failed"
mkdir -p ~/.ludilo
[ -f ~/.ludilo/android.jar ] || echo "Put an android.jar (API 34) at ~/.ludilo/android.jar (or set ANDROID_JAR)"
echo "Then: python -m ludilo config   and   python -m ludilo"
