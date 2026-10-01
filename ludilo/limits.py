"""Permissions: everything is allowed by default. Users add limits in ~/.ludilo/config.json:
  "limits": {"deny": ["device_settings"], "confirm": ["install_apk"], "deny_shell": ["rm -rf", "su "]}
"""
import fnmatch
from . import llm


def get():
    return {"deny": [], "confirm": [], "deny_shell": [], **llm.load_file().get("limits", {})}


def check(name, args):
    """-> 'allow' | 'confirm' | 'deny:<why>'"""
    lim = get()
    if any(fnmatch.fnmatch(name, p) for p in lim["deny"]):
        return f"deny:tool '{name}' is disabled by user limits"
    if name in ("run_shell", "termux_api"):
        cmd = args.get("command", "")
        for bad in lim["deny_shell"]:
            if bad in cmd:
                return f"deny:command contains blocked pattern '{bad}'"
    if any(fnmatch.fnmatch(name, p) for p in lim["confirm"]):
        return "confirm"
    return "allow"


def edit(kind, tool=None):
    cfg = llm.load_file()
    lim = {"deny": [], "confirm": [], "deny_shell": [], **cfg.get("limits", {})}
    if kind == "show":
        return lim
    for k in ("deny", "confirm"):
        if tool in lim[k]:
            lim[k].remove(tool)
    if kind in ("deny", "confirm"):
        lim[kind].append(tool)
    elif kind == "deny_shell":
        lim["deny_shell"].append(tool)
    cfg["limits"] = lim
    llm.save_file(cfg)
    return lim
