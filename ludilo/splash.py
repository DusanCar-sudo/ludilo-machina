import os, sys
from .splash_art import ART
from . import __version__

GREEN = "\033[38;2;170;255;0m"  # logo colour; plain text when not a TTY / NO_COLOR


def show(out=sys.stdout, model=""):
    color = out.isatty() and not os.environ.get("NO_COLOR")
    c, r = (GREEN, "\033[0m") if color else ("", "")
    out.write(f"{c}{ART}{r}\n")
    out.write(f"  {c}ludilo-machina{r} {__version__}  <o>  Android-native coding agent\n")
    out.write(f"  build APKs on this phone · control your device · {model or 'no model set (ludilo config)'}\n\n")
