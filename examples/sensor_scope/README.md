# Sensor Scope

A live system monitor, built and signed **on the phone** by ludilo-machina's own toolchain
(aapt2, javac, d8, zipalign, apksigner). No Gradle, no PC.

Panels with scrolling 60 s line graphs: CPU (per-core clock), temperature (thermal zones + battery),
memory, battery, network (KB/s), storage, plus a collapsed raw-sensors panel. Tap a panel to collapse it.

Notes from real hardware (Redmi Note 12 Pro, Android 13):
- Apps cannot read `/proc/stat`, so CPU load % is blocked. The graph shows each core's clock as % of its max and says so.
- Some thermal zones are not temperatures (`ibat`, `vbat`, `soc` report currents, volts, junk). They are filtered out.

Build in Termux, from the repo root:

    python -c "from ludilo import apk; print(apk.build('examples/sensor_scope'))"

Then install the printed `.apk` path.
