"""The agent loop: model <-> tools until the model stops calling tools."""
import json
from . import env, llm, tools

SYSTEM = """You are ludilo-machina, a coding agent that runs INSIDE Termux on an Android phone.
You are fully aware of your environment: use probe_env first when unsure what is installed.
You build real Android apps (Java, no Gradle) and pack them into signed APKs on this phone
with new_android_project -> write_file -> build_apk -> install_apk -> launch_app, then verify with
ui_dump/screenshot/logcat and fix errors until the app works. You can also control the phone via
device_input, device_settings and termux_api. Be economical: the device has limited RAM and battery.
Ask before anything destructive. Device profile:
{profile}"""


def run(user_msg, history=None, cfg=None, chat=llm.chat, max_steps=30, say=print):
    history = history or [{"role": "system", "content": SYSTEM.format(profile=json.dumps(env.probe()))}]
    history.append({"role": "user", "content": user_msg})
    for _ in range(max_steps):
        try:
            m = chat(history, tools.SCHEMAS, cfg) if cfg else chat(history, tools.SCHEMAS)
        except RuntimeError as e:
            say(f"[model error: {e}] - your chat is kept, just say 'continue'")
            return history
        history.append({k: v for k, v in m.items() if v is not None})
        if m.get("content"):
            say(m["content"])
        if not m.get("tool_calls"):
            return history
        for tc in m["tool_calls"]:
            f = tc["function"]
            args = json.loads(f.get("arguments") or "{}")
            say(f"  > {f['name']}({', '.join(f'{k}={str(v)[:40]!r}' for k, v in args.items())})")
            history.append({"role": "tool", "tool_call_id": tc["id"], "content": tools.call(f["name"], args)})
    say("[step limit reached]")
    return history
