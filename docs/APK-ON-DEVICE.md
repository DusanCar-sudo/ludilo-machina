# Building APKs on-device

Pipeline (no Gradle, lightweight):
1. `aapt2 compile` + `aapt2 link` resources/manifest -> base APK + R.java
2. `ecj` (or `kotlinc`) Java/Kotlin -> .class
3. `d8` .class -> classes.dex, add to APK
4. `zipalign -p 4`
5. `apksigner sign` with a locally generated keystore (`keytool`)
6. Install: `termux-open --view app.apk` (needs "Install unknown apps" for Termux)

Option B: Gradle on-device with `android.aapt2FromMavenOverride` pointing at Termux's aarch64 aapt2. Heavy on RAM.
Option C: remote/CI build fallback (GitHub Actions) when device is too weak.

Notes: use Termux from F-Droid/GitHub (Play build is outdated); Android 10+ exec limits apply to app-data binaries.
