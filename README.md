# ludilo-machina

A coding agent that runs **inside Termux on Android**. It writes Android apps, packs them into signed
APKs **on the phone**, installs them, launches them, looks at the screen/logs, and fixes what broke.

## Status (v0.1, honest)
- Done and tested on a desktop: agent loop, tool dispatch, confirmation gate, action log, project template.
- Written but **not yet run on a phone**: APK pipeline (`ludilo/apk.py`), device tools (adb/Termux:API), `scripts/setup.sh`.

## Run (in Termux)
    sh scripts/setup.sh
    python -m ludilo config      # base URL / model / key (any OpenAI-compatible API)
    python -m ludilo "make a flashlight app and install it"

## Tools the agent has
files/shell, `probe_env`, `new_android_project`, `build_apk`, `install_apk`, `launch_app`,
`screenshot`, `ui_dump`, `logcat`, `device_input`, `device_settings`, `termux_api`.
Risky ones ask for confirmation; every action is logged to `~/.ludilo/actions.log`.

See docs/ARCHITECTURE.md and docs/APK-ON-DEVICE.md.
