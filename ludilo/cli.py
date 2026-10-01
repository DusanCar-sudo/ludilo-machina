import sys
import json
from . import agent, llm, env, limits, splash


def setup_llm():
    cfg = llm.load_config()
    for k, label in (("base_url", "Base URL"), ("model", "Model"), ("api_key", "API key")):
        v = input(f"{label} [{cfg[k] if k != 'api_key' and cfg[k] else ''}]: ").strip()
        if v:
            cfg[k] = v
    llm.save_config(cfg)
    print("saved to ~/.ludilo/config.json (0600)")


def main():
    a = sys.argv[1:]
    if a[:1] == ["env"]:
        return env.main() if hasattr(env, "main") else print(__import__("json").dumps(env.probe(), indent=1))
    if a[:1] == ["config"]:
        return setup_llm()
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
    hist = None
    first = " ".join(a)
    while True:
        try:
            msg = first or input("\nludilo> ")
        except EOFError:
            return 0
        first = ""
        if msg.strip():
            hist = agent.run(msg, hist)


if __name__ == "__main__":
    sys.exit(main())
