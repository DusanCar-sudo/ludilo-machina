"""OpenAI-compatible chat client (stdlib only). User supplies base URL / model / key."""
import json, os, urllib.request

CONF = os.path.expanduser("~/.ludilo/config.json")


def load_file():
    return json.load(open(CONF)) if os.path.exists(CONF) else {}


def save_file(c):
    os.makedirs(os.path.dirname(CONF), exist_ok=True)
    with open(CONF, "w") as f:
        json.dump(c, f, indent=2)
    os.chmod(CONF, 0o600)


def load_config():
    c = load_file()
    return {"base_url": os.environ.get("LUDILO_BASE_URL", c.get("base_url", "https://api.openai.com/v1")),
            "model": os.environ.get("LUDILO_MODEL", c.get("model", "")),
            "api_key": os.environ.get("LUDILO_API_KEY", c.get("api_key", ""))}


def save_config(cfg):
    save_file({**load_file(), **cfg})


def chat(messages, tools, cfg=None):
    cfg = cfg or load_config()
    body = {"model": cfg["model"], "messages": messages}
    if tools:
        body["tools"] = [{"type": "function", "function": t} for t in tools]
    req = urllib.request.Request(cfg["base_url"].rstrip("/") + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json",
                                  "Authorization": f"Bearer {cfg['api_key']}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    record_usage(cfg["model"], data.get("usage") or {})
    return data["choices"][0]["message"]


USAGE = os.path.expanduser("~/.ludilo/usage.jsonl")
SESSION = {"prompt": 0, "completion": 0, "calls": 0}


def record_usage(model, u):
    p, c = u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
    SESSION["prompt"] += p; SESSION["completion"] += c; SESSION["calls"] += 1
    os.makedirs(os.path.dirname(USAGE), exist_ok=True)
    with open(USAGE, "a") as f:
        f.write(json.dumps({"t": int(__import__("time").time()), "model": model, "prompt": p, "completion": c}) + "\n")


def usage_totals():
    """-> {'today': (calls, prompt, completion), 'all': (...)} from the usage log."""
    import time
    day = time.time() - (time.time() % 86400)
    out = {"today": [0, 0, 0], "all": [0, 0, 0]}
    if os.path.exists(USAGE):
        for line in open(USAGE):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            for k in (("all",) if r["t"] < day else ("all", "today")):
                out[k][0] += 1; out[k][1] += r["prompt"]; out[k][2] += r["completion"]
    return out
