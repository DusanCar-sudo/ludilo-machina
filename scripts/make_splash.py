"""Render assets/ludilo-machina-logo-terminal.png to half-block text art -> ludilo/splash_art.py (stdlib only)."""
import os, struct, zlib

W = 44  # output columns
src = os.path.join(os.path.dirname(__file__), "..", "assets", "ludilo-machina-logo-terminal.png")
d = open(src, "rb").read()
p, idat, w, h = 8, b"", 0, 0
while p < len(d):
    n, t = struct.unpack(">I4s", d[p:p + 8])
    body = d[p + 8:p + 8 + n]
    if t == b"IHDR":
        w, h = struct.unpack(">II", body[:8])
    elif t == b"IDAT":
        idat += body
    p += 12 + n
raw, bpp, stride = zlib.decompress(idat), 4, w * 4
rows, prev = [], bytearray(stride)
for y in range(h):
    f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
    for i in range(stride):
        a = line[i - bpp] if i >= bpp else 0
        b = prev[i]
        c = prev[i - bpp] if i >= bpp else 0
        if f == 1: line[i] = (line[i] + a) & 255
        elif f == 2: line[i] = (line[i] + b) & 255
        elif f == 3: line[i] = (line[i] + (a + b) // 2) & 255
        elif f == 4:
            pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
            line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
    rows.append(line); prev = line
alpha = [[r[x * 4 + 3] for x in range(w)] for r in rows]
# crop to content
ys = [y for y in range(h) if max(alpha[y]) > 128]; xs = [x for x in range(w) if any(alpha[y][x] > 128 for y in ys)]
y0, y1, x0, x1 = ys[0], ys[-1] + 1, xs[0], xs[-1] + 1
cw = x1 - x0; cell = cw / W; rh = cell * 2  # each text row = 2 pixel rows (half blocks)
H = int((y1 - y0) / rh) * 2
def dens(cx, cy):
    xa, xb, ya, yb = int(x0 + cx * cell), int(x0 + (cx + 1) * cell), int(y0 + cy * rh / 2), int(y0 + (cy + 1) * rh / 2)
    s = n = 0
    for y in range(ya, min(yb, h)):
        for x in range(xa, min(xb, w)):
            s += alpha[y][x] > 128; n += 1
    return s / n > 0.5 if n else False
out = []
for r in range(0, H, 2):
    out.append("".join({(1, 1): "█", (1, 0): "▀", (0, 1): "▄", (0, 0): " "}[(dens(c, r), dens(c, r + 1))] for c in range(W)).rstrip())
art = "\n".join(out)
open(os.path.join(os.path.dirname(__file__), "..", "ludilo", "splash_art.py"), "w").write(f'ART = """\\\n{art}\n"""\n')
print(art)
