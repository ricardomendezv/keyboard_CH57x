"""Generate app.ico — a little macropad: 2 knobs on top, a 3x4 key grid below."""
from PIL import Image, ImageDraw

S = 256
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# rounded body
body = (24, 26, 34, 255)
edge = (60, 64, 82, 255)
d.rounded_rectangle([16, 16, S - 16, S - 16], radius=36, fill=body, outline=edge, width=4)

# two knobs (top)
knob = (90, 96, 120, 255)
knob_top = (140, 148, 180, 255)
for cx in (92, 164):
    d.ellipse([cx - 26, 40, cx + 26, 92], fill=knob, outline=knob_top, width=3)
    d.ellipse([cx - 9, 58, cx + 9, 76], fill=knob_top)

# 3 columns x 4 rows of keys
key = (45, 130, 210, 255)        # blue
key_hi = (80, 170, 245, 255)
accent = (235, 170, 60, 255)     # one orange accent key
cols, rows = 3, 4
x0, y0, gap, ks = 40, 108, 14, 44
for r in range(rows):
    for c in range(cols):
        x = x0 + c * (ks + gap)
        y = y0 + r * (ks + gap)
        col = accent if (r == 0 and c == 2) else key
        d.rounded_rectangle([x, y, x + ks, y + ks], radius=9, fill=col, outline=key_hi, width=2)

sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save("app.ico", sizes=sizes)
print("wrote app.ico with sizes", sizes)
