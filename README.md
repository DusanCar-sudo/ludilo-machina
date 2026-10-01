# ludilo-machina

A mobile coding agent that lives in Termux on Android and is fully aware of its environment
(Termux prefix, Android permissions, storage, battery/network, device limits).

Goal: describe an app on your phone, get a signed, installable APK built on the same phone.

## Pillars
1. **Environment-aware agent**: detects Termux vs. other, arch, free RAM/storage, installed toolchain, granted permissions; adapts plans accordingly.
2. **On-device APK pipeline**: `aapt2` -> compile (ecj/kotlinc) -> `d8` -> `zipalign` -> `apksigner` -> install via `termux-open`.
3. **Provider-agnostic LLM backend**: user supplies base URL / model / key.

See docs/APK-ON-DEVICE.md.
