"""OpenAI-compatible chat client (stdlib only). User supplies base URL / model / key."""
import json, os, urllib.request

CONF = os.path.expanduser("~/.ludilo/config.json")


def load_config():
    c = {}
    if os.path.exists(CONF):
        c = json.load(open(CONF))
    return {"base_url": os.environ.get("LUDILO_BASE_URL", c.get("base_url", "https://api.openai.com/v1")),
            "model": os.environ.get("LUDILO_MODEL", c.get("model", "")),
            "api_key": os.environ.get("LUDILO_API_KEY", c.get("api_key", ""))}


def save_config(cfg):
    os.makedirs(os.path.dirname(CONF), exist_ok=True)
    with open(CONF, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONF, 0o600)


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
        return json.load(r)["choices"][0]["message"]
