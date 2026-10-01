"""Environment probe: what device/toolchain/permissions the agent is running in."""
import json, os, platform, shutil, subprocess

TOOLS = ["aapt2", "d8", "apksigner", "zipalign", "ecj", "javac", "java", "keytool",
         "kotlinc", "adb", "termux-battery-status", "termux-screenshot"]


def _run(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def probe():
    prefix = os.environ.get("PREFIX", "")
    mem = {}
    try:
        for line in open("/proc/meminfo"):
            k, v = line.split(":")
            mem[k] = int(v.split()[0]) // 1024
    except OSError:
        pass
    st = shutil.disk_usage(os.path.expanduser("~"))
    return {
        "termux": "com.termux" in prefix,
        "arch": platform.machine(),
        "android_api": _run("getprop ro.build.version.sdk") or None,
        "device": _run("getprop ro.product.model") or None,
        "ram_free_mb": mem.get("MemAvailable"),
        "storage_free_mb": st.free // 2**20,
        "tools": {t: bool(shutil.which(t)) for t in TOOLS},
        "android_jar": next((p for p in android_jar_candidates() if os.path.exists(p)), None),
    }


def android_jar_candidates():
    home = os.path.expanduser("~")
    return [os.environ.get("ANDROID_JAR", ""), f"{home}/.ludilo/android.jar",
            os.environ.get("PREFIX", "") + "/share/java/android.jar"]


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2))
