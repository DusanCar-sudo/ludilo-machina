"""On-device APK pipeline: aapt2 -> compile -> d8 -> zip -> zipalign -> apksigner."""
import glob, os, shutil, subprocess, zipfile
from . import env

HOME = os.path.expanduser("~/.ludilo")


class BuildError(Exception):
    pass


def _sh(args, cwd=None):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        raise BuildError(f"$ {' '.join(args)}\n{r.stdout}{r.stderr}".strip())
    return r.stdout


def _need(tool):
    if not shutil.which(tool):
        raise BuildError(f"missing tool '{tool}'. In Termux run: ludilo setup")
    return tool


def zipalign(src, dst, align=4):
    """Pure-Python zipalign (Termux has no zipalign package): pad stored entries to `align` bytes."""
    with zipfile.ZipFile(src) as zi, open(dst, "wb") as out:
        zo = zipfile.ZipFile(out, "w")
        for info in zi.infolist():
            data = zi.read(info.filename)
            ni = zipfile.ZipInfo(info.filename, info.date_time)
            ni.compress_type, ni.external_attr = info.compress_type, info.external_attr
            if info.compress_type == zipfile.ZIP_STORED:
                off = out.tell() + 30 + len(info.filename.encode())
                pad = (-off) % align
                if pad:
                    ni.extra = b"\x00" * pad
            zo.writestr(ni, data)
        zo.close()


def ensure_keystore():
    ks = f"{HOME}/debug.keystore"
    if not os.path.exists(ks):
        os.makedirs(HOME, exist_ok=True)
        _sh([_need("keytool"), "-genkeypair", "-keystore", ks, "-storepass", "ludilo123",
             "-keypass", "ludilo123", "-alias", "ludilo", "-keyalg", "RSA", "-keysize", "2048",
             "-validity", "10000", "-dname", "CN=ludilo"])
    return ks


def build(project, out=None):
    """Build `project` (dir with AndroidManifest.xml, src/, res/) into a signed APK. Returns path."""
    project = os.path.abspath(project)
    jar = next((p for p in env.android_jar_candidates() if p and os.path.exists(p)), None)
    if not jar:
        raise BuildError("android.jar not found. Run: ludilo setup (or set ANDROID_JAR)")
    b = f"{project}/build"
    shutil.rmtree(b, ignore_errors=True)
    for d in ("compiled", "gen", "classes"):
        os.makedirs(f"{b}/{d}")
    res = f"{project}/res"
    if os.path.isdir(res):
        _sh([_need("aapt2"), "compile", "--dir", res, "-o", f"{b}/compiled"])
    flats = glob.glob(f"{b}/compiled/*.flat")
    base = f"{b}/base.apk"
    _sh([_need("aapt2"), "link", "-o", base, "-I", jar, "--manifest", f"{project}/AndroidManifest.xml",
         "--java", f"{b}/gen", "--auto-add-overlay", *flats])
    srcs = glob.glob(f"{project}/src/**/*.java", recursive=True) + glob.glob(f"{b}/gen/**/*.java", recursive=True)
    if shutil.which("javac"):
        _sh(["javac", "-nowarn", "--release", "8", "-d", f"{b}/classes", "-cp", jar, *srcs])
    else:
        _sh([_need("ecj"), "-nowarn", "-d", f"{b}/classes", "-cp", jar, *srcs])
    classes = glob.glob(f"{b}/classes/**/*.class", recursive=True)
    _sh([_need("d8"), "--lib", jar, "--output", b, *classes])
    with zipfile.ZipFile(base, "a") as z:
        z.write(f"{b}/classes.dex", "classes.dex")
    name = os.path.basename(project)
    aligned = f"{b}/aligned.apk"
    if shutil.which("zipalign"):
        _sh(["zipalign", "-f", "-p", "4", base, aligned])
    else:
        zipalign(base, aligned)
    final = out or f"{project}/{name}.apk"
    _sh([_need("apksigner"), "sign", "--ks", ensure_keystore(), "--ks-pass", "pass:ludilo123",
         "--out", final, aligned])
    return final


def package_name(project):
    import re
    m = re.search(r'package="([^"]+)"', open(f"{project}/AndroidManifest.xml").read())
    return m.group(1) if m else None


def new_project(dest, name="hello", package="com.ludilo.hello"):
    """Copy the hello template to dest, renaming the package."""
    t = os.path.join(os.path.dirname(__file__), "..", "templates", "hello")
    shutil.copytree(t, dest)
    old = "com.ludilo.hello"
    if package != old:
        olddir = f"{dest}/src/{old.replace('.', '/')}"
        newdir = f"{dest}/src/{package.replace('.', '/')}"
        os.makedirs(os.path.dirname(newdir), exist_ok=True)
        shutil.move(olddir, newdir)
        for p in glob.glob(f"{dest}/**/*", recursive=True):
            if os.path.isfile(p):
                s = open(p).read()
                if old in s:
                    open(p, "w").write(s.replace(old, package))
    return dest
