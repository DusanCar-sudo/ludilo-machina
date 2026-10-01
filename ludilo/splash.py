import os, sys
from .splash_art import ART
from . import __version__

GOLD = "\033[38;2;231;207;133m"   # Aura Nature palette; plain text when not a TTY / NO_COLOR
CREAM = "\033[38;2;242;235;201m"
STRIPES = "".join(f"\033[38;2;{c}m\u2588\u2588\033[0m" for c in ("228;49;43", "248;185;30", "47;174;78", "26;166;224"))


def show(out=sys.stdout, model=""):
    color = out.isatty() and not os.environ.get("NO_COLOR")
    c, w, r = (GOLD, CREAM, "\033[0m") if color else ("", "", "")
    out.write(f"{c}{ART}{r}\n")
    out.write(f"  {w}ludilo-machina{r} {__version__}  <o>  Android-native coding agent  {STRIPES if color else ''}\n")
    out.write(f"  build APKs on this phone · control your device · {model or 'no model set (ludilo config)'}\n\n")
