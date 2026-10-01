# ludilo-machina agent rules
- Target: Termux on Android (aarch64). Never assume root or desktop tools.
- Detect env first (scripts/env-probe.sh); plan within RAM/storage limits.
- APK pipeline lives in scripts/; keep it Gradle-free by default.
- Repo root only; one page of docs per topic in docs/.
