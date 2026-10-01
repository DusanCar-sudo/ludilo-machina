import sys
from . import agent, llm, env, __version__


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
    if not llm.load_config()["model"]:
        print("No model configured. Run: ludilo config")
        return 1
    print(f"ludilo-machina {__version__} - Android coding agent. Ctrl-D to exit.")
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
