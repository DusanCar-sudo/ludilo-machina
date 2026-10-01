# Architecture: Android-native agent

Vision: first coding agent built for Android. It writes the app AND operates the phone to build, install, launch, test and fix it.

## Control layers (least to most privilege)
1. **Termux core**: shell, files, toolchain (no extra permissions).
2. **Termux:API**: camera, sensors, location, notifications, clipboard, TTS, SMS/call log, volume, brightness, vibrate, wifi info, share/open.
3. **Intents via `am` / `termux-open`**: launch apps, deep links, settings screens, share sheets.
4. **Self-ADB (wireless debugging, pair to localhost)**: no root. Gives `pm install -r` (silent install), `input tap/swipe/text`, `screencap`, `uiautomator dump` (read the UI tree), `settings put`, `logcat`, `am force-stop`, `cmd package`.
5. **Shizuku** (optional): same shell power with simpler re-activation.
6. **Companion app "ludilo-hand"** (built by this very pipeline): AccessibilityService for robust UI control + notification listener, exposes a local socket/HTTP API to the agent.

## The loop (build -> deploy -> test on the same phone)
plan -> generate project -> build APK -> `pm install` -> `am start` -> `screencap` + `uiautomator dump` -> compare to intent -> `logcat` errors -> patch -> repeat.

## Safety model
- Read-only by default; confirm before: SMS/calls, installs of other apps, settings changes, deleting files.
- Action log (append-only) of every device action.
- Kill switch: Termux notification action + volume-key combo.

## Environment awareness
`env-probe` -> device profile JSON (arch, Android API, RAM, storage, battery, network, granted tiers, installed tools) injected into every agent plan.
