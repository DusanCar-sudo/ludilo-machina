import json, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ludilo import agent, tools


def test_loop_creates_project_and_stops():
    d = tempfile.mkdtemp() + "/app"
    script = iter([
        {"role": "assistant", "content": "creating", "tool_calls": [
            {"id": "1", "type": "function", "function": {"name": "new_android_project",
             "arguments": json.dumps({"dest": d, "package": "com.x.demo"})}}]},
        {"role": "assistant", "content": "done"},
    ])
    out = []
    h = agent.run("make an app", chat=lambda m, t, *a: next(script), say=out.append)
    assert os.path.exists(f"{d}/src/com/x/demo/MainActivity.java")
    assert 'package="com.x.demo"' in open(f"{d}/AndroidManifest.xml").read()
    assert h[-1]["content"] == "done"


def test_allow_all_by_default_then_user_limits():
    from ludilo import limits, llm
    llm.CONF = tempfile.mkdtemp() + "/config.json"
    never = lambda d: (_ for _ in ()).throw(AssertionError("must not prompt by default"))
    assert tools.call("run_shell", {"command": "echo hi"}, confirm=never) == "hi"
    limits.edit("confirm", "run_shell")
    assert tools.call("run_shell", {"command": "echo hi"}, confirm=lambda d: False) == "DENIED by user"
    limits.edit("deny", "run_shell")
    assert tools.call("run_shell", {"command": "echo hi"}).startswith("BLOCKED")
    limits.edit("allow", "run_shell"); limits.edit("deny_shell", "rm -rf")
    assert tools.call("run_shell", {"command": "rm -rf /x"}).startswith("BLOCKED")
    assert tools.call("run_shell", {"command": "echo ok"}) == "ok"
