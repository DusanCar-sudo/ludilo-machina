import sys
import glob, json, os, time
from . import agent, llm, env, limits, splash


def setup_llm():
    cfg = llm.load_config()
    for k, label in (("base_url", "Base URL"), ("model", "Model"), ("api_key", "API key")):
        v = input(f"{label} [{cfg[k] if k != 'api_key' and cfg[k] else ''}]: ").strip()
        if v:
            cfg[k] = v
    llm.save_config(cfg)
    print("saved to ~/.ludilo/config.json (0600)")


SESS = os.path.expanduser("~/.ludilo/sessions")


def _sessions():
    return sorted(glob.glob(f"{SESS}/*.json"), reverse=True)


def _save(path, hist):
    os.makedirs(SESS, exist_ok=True)
    json.dump(hist, open(path, "w"))


def _pick(arg):
    """'continue' -> newest; 'resume' -> numbered menu; 'resume N' -> Nth."""
    ss = _sessions()
    if not ss:
        print("no saved sessions yet"); return None
    if arg == "continue":
        return ss[0]
    if arg and arg.isdigit() and 0 < int(arg) <= len(ss):
        return ss[int(arg) - 1]
    for i, f in enumerate(ss[:15], 1):
        h = json.load(open(f))
        first = next((m["content"] for m in h if m["role"] == "user"), "")[:70].replace("\n", " ")
        print(f"{i:>2}. {os.path.basename(f)[:-5]}  {first}")
    n = input("resume which? ").strip()
    return ss[int(n) - 1] if n.isdigit() and 0 < int(n) <= len(ss) else None


def status():
    cfg, t = llm.load_config(), llm.usage_totals()
    tools = env.probe()["tools"]
    print(f"model     {cfg['model'] or '(not set)'}\nendpoint  {cfg['base_url']}\napi key   {'set' if cfg['api_key'] else 'MISSING'}")
    print("toolchain " + " ".join(f"{k}{'✓' if v else '✗'}" for k, v in tools.items() if k in ("aapt2", "d8", "apksigner", "javac")))
    lim = {k: v for k, v in limits.get().items() if v}
    print("limits    " + (json.dumps(lim) if lim else "none") + "  (allow-all by default)")
    for k in ("today", "all"):
        n, p, c = t[k]
        print(f"tokens {k:5} {p + c:>10,}  (in {p:,} / out {c:,}, {n} calls)")


def main():
    a = sys.argv[1:]
    if a[:1] == ["env"]:
        return env.main() if hasattr(env, "main") else print(__import__("json").dumps(env.probe(), indent=1))
    if a[:1] == ["config"]:
        return setup_llm()
    if a[:1] in (["status"], ["usage"]):
        return status()
    if a[:1] == ["limits"]:
        if len(a) == 1:
            return print(json.dumps(limits.get(), indent=1))
        if a[1] not in ("deny", "confirm", "allow", "deny_shell") or len(a) < 3:
            return print("usage: ludilo limits [deny|confirm|allow|deny_shell] <tool or pattern>")
        return print(json.dumps(limits.edit(a[1], " ".join(a[2:])), indent=1))
    if not llm.load_config()["model"]:
        print("No model configured. Run: ludilo config")
        return 1
    splash.show(model=llm.load_config()["model"])
    hist, path = None, f"{SESS}/{time.strftime('%Y%m%d-%H%M%S')}.json"
    if a[:1] in (["continue"], ["resume"]):
        f = _pick(a[0] if a[0] == "continue" else (a[1] if len(a) > 1 else ""))
        if f:
            hist, path = json.load(open(f)), f
            print(f"resumed {os.path.basename(f)} ({len(hist)} messages)")
        a = []
    first = " ".join(a)
    while True:
        try:
            msg = first or input("\nludilo> ")
        except EOFError:
            S = llm.SESSION
            print(f"\nsession: {S['prompt'] + S['completion']:,} tokens ({S['calls']} calls)")
            return 0
        first = ""
        if msg.strip():
            hist = agent.run(msg, hist)
            _save(path, hist)


if __name__ == "__main__":
    sys.exit(main())
