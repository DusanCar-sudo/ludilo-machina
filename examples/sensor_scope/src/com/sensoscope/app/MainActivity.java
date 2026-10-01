package com.sensoscope.app;

import android.app.Activity;
import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Typeface;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.net.TrafficStats;
import android.os.BatteryManager;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.StatFs;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.Locale;

/** Sensor Scope: a live system monitor (CPU, temperature, memory, battery, network, storage, sensors). */
public class MainActivity extends Activity implements SensorEventListener {
    static final int N = 60;                       // samples kept per line (1 Hz)
    static final int BG = 0xFF0B0F14, CARD = 0xFF111820, TXT = 0xFFE6EDF3, DIM = 0xFF8B98A5;
    static final int[] COLORS = {0xFF39C5F0, 0xFF4ADE80, 0xFFFACC15, 0xFFFB923C, 0xFFF87171,
            0xFFC084FC, 0xFF2DD4BF, 0xFFF472B6, 0xFF94A3B8};

    final Handler h = new Handler();
    int dp;
    Panel cpu, temp, mem, bat, net, sto;
    TextView sensorsText, storageText, cpuNote;
    long[] lastStat; long lastRx, lastTx, lastT;
    int cores; int[] maxFreq;
    SensorManager sm;
    float[] acc = new float[3], gyr = new float[3]; float light = -1, prox = -1, proxMax = 5;
    boolean haveAcc, haveGyr, haveLight, haveProx;
    final ArrayList<Integer> zones = new ArrayList<>();
    final ArrayList<String> zoneNames = new ArrayList<>();

    // ---------------------------------------------------------------- graph view
    static class Graph extends View {
        final Paint line = new Paint(Paint.ANTI_ALIAS_FLAG), fill = new Paint(), grid = new Paint(), txt = new Paint(Paint.ANTI_ALIAS_FLAG);
        final ArrayList<float[]> data = new ArrayList<>();   // each: ring buffer of N
        final ArrayList<Integer> cols = new ArrayList<>();
        float fixedMin = Float.NaN, fixedMax = Float.NaN; String unit = ""; int count = 0;

        Graph(Context c, float density) {
            super(c);
            line.setStyle(Paint.Style.STROKE); line.setStrokeWidth(2f * density);
            line.setStrokeJoin(Paint.Join.ROUND);
            fill.setStyle(Paint.Style.FILL);
            grid.setColor(0x22FFFFFF); grid.setStrokeWidth(1f);
            txt.setColor(DIM); txt.setTextSize(10f * density); txt.setTypeface(Typeface.MONOSPACE);
        }

        int series(int color) {
            data.add(new float[N]); cols.add(color); return data.size() - 1;
        }

        void push(int s, float v) {
            float[] a = data.get(s);
            System.arraycopy(a, 1, a, 0, N - 1); a[N - 1] = v;
        }

        void tick() { if (count < N) count++; invalidate(); }

        @Override protected void onDraw(Canvas cv) {
            int w = getWidth(), hgt = getHeight();
            float mn = Float.MAX_VALUE, mx = -Float.MAX_VALUE;
            for (float[] a : data) for (int i = N - count; i < N; i++) { mn = Math.min(mn, a[i]); mx = Math.max(mx, a[i]); }
            if (mn > mx) { mn = 0; mx = 1; }
            if (!Float.isNaN(fixedMin)) mn = fixedMin;
            if (!Float.isNaN(fixedMax)) mx = fixedMax;
            else { float pad = Math.max((mx - mn) * 0.15f, 0.5f); mx += pad; if (Float.isNaN(fixedMin)) mn = Math.max(0, mn - pad); }
            if (mx - mn < 1e-3f) mx = mn + 1;
            for (int g = 0; g <= 3; g++) { float y = hgt * g / 3f; cv.drawLine(0, y, w, y, grid); }
            for (int s = 0; s < data.size(); s++) {
                float[] a = data.get(s);
                Path p = new Path(), f = new Path(); boolean first = true;
                for (int i = N - count; i < N; i++) {
                    float x = w * i / (float) (N - 1);
                    float y = hgt - (a[i] - mn) / (mx - mn) * hgt;
                    y = Math.max(1, Math.min(hgt - 1, y));
                    if (first) { p.moveTo(x, y); f.moveTo(x, hgt); f.lineTo(x, y); first = false; }
                    else { p.lineTo(x, y); f.lineTo(x, y); }
                    if (i == N - 1) f.lineTo(x, hgt);
                }
                int c = cols.get(s);
                if (data.size() <= 2) { fill.setColor((c & 0x00FFFFFF) | 0x33000000); cv.drawPath(f, fill); }
                line.setColor(c); cv.drawPath(p, line);
            }
            cv.drawText(String.format(Locale.US, "%.0f%s", mx, unit), 4, txt.getTextSize(), txt);
            cv.drawText(String.format(Locale.US, "%.0f%s", mn, unit), 4, hgt - 4, txt);
        }
    }

    // ---------------------------------------------------------------- collapsible panel
    class Panel {
        final LinearLayout box = new LinearLayout(MainActivity.this);
        final TextView title, value, legend;
        final Graph graph;
        final LinearLayout body = new LinearLayout(MainActivity.this);

        Panel(String name, int accent, float min, float max, String unit) {
            box.setOrientation(LinearLayout.VERTICAL);
            box.setBackgroundColor(CARD);
            box.setPadding(dp * 14, dp * 12, dp * 14, dp * 12);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
            lp.setMargins(dp * 12, dp * 6, dp * 12, dp * 6);
            box.setLayoutParams(lp);
            LinearLayout head = new LinearLayout(MainActivity.this);
            head.setOrientation(LinearLayout.HORIZONTAL); head.setGravity(Gravity.CENTER_VERTICAL);
            title = tv(name.toUpperCase(Locale.US), 13, accent, true);
            value = tv("-", 22, TXT, true);
            value.setGravity(Gravity.END);
            head.addView(title, new LinearLayout.LayoutParams(0, -2, 1));
            head.addView(value, new LinearLayout.LayoutParams(0, -2, 2));
            box.addView(head);
            body.setOrientation(LinearLayout.VERTICAL);
            graph = new Graph(MainActivity.this, dp);
            graph.fixedMin = min; graph.fixedMax = max; graph.unit = unit;
            body.addView(graph, new LinearLayout.LayoutParams(-1, dp * 110));
            legend = tv("", 11, DIM, false);
            body.addView(legend);
            box.addView(body);
            head.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) { body.setVisibility(body.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE); }
            });
        }
    }

    TextView tv(String s, int sp, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(s); t.setTextSize(sp); t.setTextColor(color); t.setTypeface(Typeface.MONOSPACE, bold ? Typeface.BOLD : Typeface.NORMAL);
        return t;
    }

    // ---------------------------------------------------------------- helpers
    static String read(String path) {
        try (BufferedReader r = new BufferedReader(new FileReader(path))) { return r.readLine(); }
        catch (Throwable e) { return null; }
    }

    static long readLong(String path) {
        String s = read(path);
        try { return s == null ? -1 : Long.parseLong(s.trim()); } catch (Throwable e) { return -1; }
    }

    long[] cpuStat() {                       // {idle, total} or null if blocked (Android 8+)
        String s = read("/proc/stat");
        if (s == null || !s.startsWith("cpu")) return null;
        try {
            String[] p = s.trim().split("\\s+"); long tot = 0;
            for (int i = 1; i < p.length; i++) tot += Long.parseLong(p[i]);
            return new long[]{Long.parseLong(p[4]) + (p.length > 5 ? Long.parseLong(p[5]) : 0), tot};
        } catch (Throwable e) { return null; }
    }

    // ---------------------------------------------------------------- lifecycle
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        dp = (int) getResources().getDisplayMetrics().density;
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        setTitle("Sensor Scope");
        cores = Runtime.getRuntime().availableProcessors();

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(BG);
        TextView head = tv("SENSOR SCOPE", 20, TXT, true);
        head.setPadding(dp * 16, dp * 18, dp * 16, dp * 2);
        root.addView(head);
        TextView sub = tv("live system monitor  -  tap a panel to collapse", 11, DIM, false);
        sub.setPadding(dp * 16, 0, dp * 16, dp * 6);
        root.addView(sub);

        // CPU: one line per core (frequency as % of that core's max) + load line if /proc/stat is readable
        cpu = new Panel("CPU", COLORS[0], 0, 100, "%");
        maxFreq = new int[cores];
        for (int i = 0; i < cores; i++) {
            cpu.graph.series(COLORS[(i + 1) % COLORS.length]);
            maxFreq[i] = (int) readLong("/sys/devices/system/cpu/cpu" + i + "/cpufreq/cpuinfo_max_freq");
        }
        cpu.graph.series(0xFFFFFFFF);                       // last series = overall load
        cpuNote = tv("", 11, DIM, false);
        cpu.body.addView(cpuNote);
        root.addView(cpu.box);

        // TEMPERATURE: all readable thermal zones + battery
        temp = new Panel("Temperature", COLORS[3], Float.NaN, Float.NaN, "C");
        for (int i = 0; i < 80 && zones.size() < 7; i++) {
            long t = readLong("/sys/class/thermal/thermal_zone" + i + "/temp");
            float c0 = t > 200 ? t / 1000f : t;
            String type = read("/sys/class/thermal/thermal_zone" + i + "/type");
            String ty = type == null ? "" : type.toLowerCase(Locale.US);
            boolean power = ty.contains("ibat") || ty.contains("vbat") || ty.contains("vph") || ty.contains("soc");
            if (t > 0 && !power && c0 >= 10 && c0 <= 120) {
                zones.add(i); zoneNames.add(type == null ? "zone" + i : type.trim());
                temp.graph.series(COLORS[(zones.size() + 2) % COLORS.length]);
            }
        }
        temp.graph.series(0xFFFFFFFF);                      // last = battery temp
        root.addView(temp.box);

        mem = new Panel("Memory", COLORS[5], 0, 100, "%");
        mem.graph.series(COLORS[5]);
        root.addView(mem.box);

        bat = new Panel("Battery", COLORS[1], 0, 100, "%");
        bat.graph.series(COLORS[1]);
        root.addView(bat.box);

        net = new Panel("Network", COLORS[2], Float.NaN, Float.NaN, "K");
        net.graph.series(COLORS[0]); net.graph.series(COLORS[3]);
        net.legend.setText("cyan = download   orange = upload   (KB/s)");
        root.addView(net.box);

        sto = new Panel("Storage", COLORS[6], 0, 100, "%");
        sto.graph.setVisibility(View.GONE);
        storageText = tv("", 12, TXT, false);
        sto.body.addView(storageText);
        root.addView(sto.box);

        Panel sen = new Panel("Raw sensors", DIM, 0, 1, "");
        sen.graph.setVisibility(View.GONE);
        sensorsText = tv("waiting for sensors...", 12, TXT, false);
        sen.body.addView(sensorsText);
        sen.body.setVisibility(View.GONE);                   // collapsed by default
        sen.value.setText("tap");
        root.addView(sen.box);

        ScrollView sv = new ScrollView(this);
        sv.setBackgroundColor(BG);
        sv.addView(root, new ViewGroup.LayoutParams(-1, -2));
        setContentView(sv);

        sm = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        lastRx = TrafficStats.getTotalRxBytes(); lastTx = TrafficStats.getTotalTxBytes(); lastT = System.nanoTime();
        lastStat = cpuStat();
    }

    @Override protected void onResume() {
        super.onResume();
        int[] types = {Sensor.TYPE_ACCELEROMETER, Sensor.TYPE_GYROSCOPE, Sensor.TYPE_LIGHT, Sensor.TYPE_PROXIMITY};
        for (int t : types) { Sensor s = sm.getDefaultSensor(t); if (s != null) sm.registerListener(this, s, SensorManager.SENSOR_DELAY_UI); }
        h.post(tick);
    }

    @Override protected void onPause() {
        super.onPause(); sm.unregisterListener(this); h.removeCallbacks(tick);
    }

    @Override public void onSensorChanged(SensorEvent e) {
        switch (e.sensor.getType()) {
            case Sensor.TYPE_ACCELEROMETER: acc = e.values.clone(); haveAcc = true; break;
            case Sensor.TYPE_GYROSCOPE: gyr = e.values.clone(); haveGyr = true; break;
            case Sensor.TYPE_LIGHT: light = e.values[0]; haveLight = true; break;
            case Sensor.TYPE_PROXIMITY: prox = e.values[0]; proxMax = e.sensor.getMaximumRange(); haveProx = true; break;
        }
    }

    @Override public void onAccuracyChanged(Sensor s, int a) { }

    // ---------------------------------------------------------------- 1 Hz sampler
    final Runnable tick = new Runnable() {
        public void run() {
            try { sample(); } catch (Throwable ignored) { }
            h.postDelayed(this, 1000);
        }
    };

    void sample() {
        // ---- CPU
        StringBuilder cl = new StringBuilder(); float avg = 0; int ok = 0;
        for (int i = 0; i < cores; i++) {
            long f = readLong("/sys/devices/system/cpu/cpu" + i + "/cpufreq/scaling_cur_freq");
            float pct = (f > 0 && maxFreq[i] > 0) ? 100f * f / maxFreq[i] : 0;
            cpu.graph.push(i, pct);
            if (f > 0) { avg += pct; ok++; cl.append(String.format(Locale.US, "cpu%d %4d MHz  ", i, f / 1000)); if (i % 2 == 1) cl.append("\n"); }
        }
        long[] st = cpuStat(); float load = -1;
        if (st != null && lastStat != null && st[1] > lastStat[1]) load = 100f * (1f - (float) (st[0] - lastStat[0]) / (st[1] - lastStat[1]));
        if (st != null) lastStat = st;
        float shown = load >= 0 ? load : (ok > 0 ? avg / ok : 0);
        cpu.graph.push(cores, load >= 0 ? load : 0);
        cpu.value.setText(String.format(Locale.US, "%.0f%%", shown));
        cpu.legend.setText(cl.toString());
        cpuNote.setText(load >= 0 ? "white = total load, colored = per-core clock as % of max"
                : ok > 0 ? "load % is blocked on this Android; lines = per-core clock as % of max"
                : "cpu frequency files are not readable by apps on this phone");
        cpu.graph.tick();

        // ---- Temperature
        StringBuilder tl = new StringBuilder(); float hottest = 0;
        for (int k = 0; k < zones.size(); k++) {
            long t = readLong("/sys/class/thermal/thermal_zone" + zones.get(k) + "/temp");
            float c = t > 200 ? t / 1000f : t;
            temp.graph.push(k, c); hottest = Math.max(hottest, c);
            tl.append(String.format(Locale.US, "%s %.1fC   ", zoneNames.get(k), c));
        }
        Intent bi = registerReceiver(null, new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
        float bt = bi == null ? 0 : bi.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0) / 10f;
        temp.graph.push(zones.size(), bt);
        tl.append(String.format(Locale.US, "battery %.1fC (white)", bt));
        temp.value.setText(String.format(Locale.US, "%.1fC", Math.max(hottest, bt)));
        temp.legend.setText(tl.toString());
        temp.graph.tick();

        // ---- Memory
        ActivityManager am = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
        ActivityManager.MemoryInfo mi = new ActivityManager.MemoryInfo(); am.getMemoryInfo(mi);
        float used = 100f * (mi.totalMem - mi.availMem) / mi.totalMem;
        mem.graph.push(0, used);
        mem.value.setText(String.format(Locale.US, "%.0f%%", used));
        mem.legend.setText(String.format(Locale.US, "used %d MB of %d MB   free %d MB%s", (mi.totalMem - mi.availMem) >> 20, mi.totalMem >> 20, mi.availMem >> 20, mi.lowMemory ? "   LOW MEMORY" : ""));
        mem.graph.tick();

        // ---- Battery
        if (bi != null) {
            int lvl = bi.getIntExtra(BatteryManager.EXTRA_LEVEL, 0), sc = bi.getIntExtra(BatteryManager.EXTRA_SCALE, 100);
            int status = bi.getIntExtra(BatteryManager.EXTRA_STATUS, 0), volt = bi.getIntExtra(BatteryManager.EXTRA_VOLTAGE, 0);
            float pct = 100f * lvl / sc;
            bat.graph.push(0, pct);
            bat.value.setText(String.format(Locale.US, "%.0f%%", pct));
            BatteryManager bm = (BatteryManager) getSystemService(Context.BATTERY_SERVICE);
            long cur = bm.getLongProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW);
            bat.legend.setText(String.format(Locale.US, "%s   %d mV   %d mA   %.1fC",
                    status == BatteryManager.BATTERY_STATUS_CHARGING ? "charging" : status == BatteryManager.BATTERY_STATUS_FULL ? "full" : "discharging",
                    volt, Math.abs(cur) / 1000, bt));
        }
        bat.graph.tick();

        // ---- Network (KB/s)
        long rx = TrafficStats.getTotalRxBytes(), tx = TrafficStats.getTotalTxBytes(), now = System.nanoTime();
        float dt = (now - lastT) / 1e9f;
        if (dt > 0 && rx >= 0 && lastRx >= 0) {
            float d = (rx - lastRx) / 1024f / dt, u = (tx - lastTx) / 1024f / dt;
            net.graph.push(0, d); net.graph.push(1, u);
            net.value.setText(String.format(Locale.US, "%.0f / %.0f KB/s", d, u));
        }
        lastRx = rx; lastTx = tx; lastT = now;
        net.graph.tick();

        // ---- Storage
        storageText.setText(bar("internal /data", Environment.getDataDirectory()) + "\n" + bar("shared /sdcard", Environment.getExternalStorageDirectory()));
        File d = Environment.getDataDirectory();
        StatFs sf = new StatFs(d.getPath());
        sto.value.setText(String.format(Locale.US, "%.0f%%", 100f * (sf.getBlockCountLong() - sf.getAvailableBlocksLong()) / sf.getBlockCountLong()));

        // ---- Raw sensors
        sensorsText.setText(String.format(Locale.US,
                "accel  %+.2f %+.2f %+.2f m/s2\ngyro   %+.3f %+.3f %+.3f rad/s\nlight  %s\nprox   %s",
                acc[0], acc[1], acc[2], gyr[0], gyr[1], gyr[2],
                haveLight ? String.format(Locale.US, "%.1f lx", light) : "none",
                haveProx ? (prox < proxMax ? "NEAR" : "far") + String.format(Locale.US, " (%.1f cm)", prox) : "none"));
    }

    String bar(String name, File f) {
        try {
            StatFs s = new StatFs(f.getPath());
            long tot = s.getBlockCountLong() * s.getBlockSizeLong(), free = s.getAvailableBlocksLong() * s.getBlockSizeLong();
            int fill = (int) (20L * (tot - free) / tot);
            StringBuilder b = new StringBuilder("[");
            for (int i = 0; i < 20; i++) b.append(i < fill ? '#' : '.');
            return String.format(Locale.US, "%s\n%s] %.1f / %.1f GB", name, b, (tot - free) / 1e9, tot / 1e9);
        } catch (Throwable e) { return name + ": unreadable"; }
    }
}
