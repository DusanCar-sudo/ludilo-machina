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


def test_confirm_denied_blocks_tool():
    assert tools.call("run_shell", {"command": "echo hi"}, confirm=lambda d: False) == "DENIED by user"
    assert tools.call("run_shell", {"command": "echo hi"}, confirm=lambda d: True) == "hi"
