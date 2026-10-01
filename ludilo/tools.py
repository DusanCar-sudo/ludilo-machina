"""Tools the agent can call. Device tools are tiered; tier >= CONFIRM asks the user first."""
import json, os, shlex, subprocess, time
from . import apk, env

LOG = os.path.expanduser("~/.ludilo/actions.log")
CONFIRM = {"install_apk", "device_input", "device_settings", "termux_api", "run_shell"}
_confirm = lambda desc: input(f"\n[ludilo] allow: {desc}? [y/N] ").strip().lower() == "y"


def sh(cmd, timeout=120):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return (r.stdout + r.stderr).strip()[-6000:] or f"(exit {r.returncode})"


def _p(path):
    return os.path.expanduser(path)


def read_file(path):
    return open(_p(path)).read()[:20000]


def write_file(path, content):
    path = _p(path)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    open(path, "w").write(content)
    return f"wrote {len(content)} bytes to {path}"


def list_dir(path="."):
    return "\n".join(sorted(os.listdir(_p(path))))


def probe_env():
    return json.dumps(env.probe(), indent=1)


def new_android_project(dest, package="com.ludilo.app"):
    apk.new_project(_p(dest), package=package)
    return f"project created at {_p(dest)} (edit AndroidManifest.xml, src/, res/)"


def build_apk(project):
    try:
        return "built: " + apk.build(_p(project))
    except apk.BuildError as e:
        return f"BUILD FAILED:\n{e}"


def install_apk(apk_path):
    """Silent install via self-ADB if connected, else open the system installer."""
    apk_path = _p(apk_path)
    if "device" in sh("adb devices | tail -n +2"):
        return sh(f"adb install -r {shlex.quote(apk_path)}")
    return sh(f"termux-open --view {shlex.quote(apk_path)}") + " (system installer opened; user taps Install)"


def launch_app(package):
    return sh(f"adb shell monkey -p {shlex.quote(package)} -c android.intent.category.LAUNCHER 1")


def screenshot(path="~/.ludilo/screen.png"):
    path = _p(path)
    return sh(f"adb exec-out screencap -p > {shlex.quote(path)}") + f" saved {path}"


def ui_dump():
    sh("adb shell uiautomator dump /sdcard/ui.xml")
    return sh("adb shell cat /sdcard/ui.xml")[-6000:]


def logcat(lines=80, package=""):
    return sh(f"adb logcat -d -t {int(lines)} | grep -i -E '{package or 'AndroidRuntime|FATAL'}'")


def device_input(action, args=""):
    """action: tap|swipe|text|key  e.g. tap '540 1200', text 'hello', key KEYCODE_BACK"""
    return sh(f"adb shell input {action} {args}")


def device_settings(namespace, key, value):
    return sh(f"adb shell settings put {shlex.quote(namespace)} {shlex.quote(key)} {shlex.quote(value)}")


def termux_api(command):
    """Run a termux-* API command (e.g. termux-battery-status, termux-notification --title hi)."""
    if not command.startswith("termux-"):
        return "only termux-* commands allowed"
    return sh(command)


def run_shell(command):
    return sh(command)


def _s(name, desc, props=None, req=None):
    return {"name": name, "description": desc,
            "parameters": {"type": "object", "properties": props or {}, "required": req or []}}


_str = {"type": "string"}
SCHEMAS = [
    _s("probe_env", "Device/toolchain profile: arch, Android API, RAM, storage, installed build tools."),
    _s("read_file", "Read a text file.", {"path": _str}, ["path"]),
    _s("write_file", "Write a file (creates dirs).", {"path": _str, "content": _str}, ["path", "content"]),
    _s("list_dir", "List a directory.", {"path": _str}),
    _s("run_shell", "Run a shell command in Termux.", {"command": _str}, ["command"]),
    _s("new_android_project", "Create a buildable Android project from template.", {"dest": _str, "package": _str}, ["dest"]),
    _s("build_apk", "Compile, dex, align and sign the project into an APK on this phone.", {"project": _str}, ["project"]),
    _s("install_apk", "Install an APK on this phone.", {"apk_path": _str}, ["apk_path"]),
    _s("launch_app", "Launch an installed app by package name.", {"package": _str}, ["package"]),
    _s("screenshot", "Capture the screen to a PNG file.", {"path": _str}),
    _s("ui_dump", "Dump the current screen's UI hierarchy (XML) to see what is displayed."),
    _s("logcat", "Recent crash/log lines, optionally filtered by package.", {"lines": {"type": "integer"}, "package": _str}),
    _s("device_input", "Send input: tap/swipe/text/key.", {"action": _str, "args": _str}, ["action"]),
    _s("device_settings", "Change an Android setting (namespace system|secure|global).", {"namespace": _str, "key": _str, "value": _str}, ["namespace", "key", "value"]),
    _s("termux_api", "Call a termux-* API command (camera, location, notification, battery, tts...).", {"command": _str}, ["command"]),
]


def call(name, args, confirm=None):
    confirm = confirm or _confirm
    fn = globals().get(name)
    if not fn or name not in {s["name"] for s in SCHEMAS}:
        return f"unknown tool {name}"
    if name in CONFIRM and not confirm(f"{name} {json.dumps(args)}"):
        out = "DENIED by user"
    else:
        try:
            out = str(fn(**args))
        except Exception as e:
            out = f"ERROR: {e}"
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{time.strftime('%F %T')} {name} {json.dumps(args)[:300]}\n")
    return out
