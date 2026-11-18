"""
Generates realistic-looking synthetic plant leaf images for demo purposes.
Covers the 3 worked examples from the PDF presentation:
  Example 1 — Tomato Late Blight   (already exists, skip)
  Example 2 — Potato Early Blight  (concentric dark rings / target-board pattern)
  Example 3 — Apple Black Rot      (purple-brown circular lesions with dark border)
"""

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import random, math, os

OUT = r"c:\Users\DELL\Desktop\Fasal-Mitra\DEMO_IMAGES"
os.makedirs(OUT, exist_ok=True)

random.seed(42)

# ─── helpers ─────────────────────────────────────────────────────────────────

def noise(img, amount=15):
    """Add pixel-level noise for realism."""
    import numpy as np
    arr = np.array(img, dtype=np.int16)
    n = np.random.randint(-amount, amount, arr.shape)
    arr = np.clip(arr + n, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def leaf_base(w, h, base_color, vein_color):
    """Draw a green leaf background with veins."""
    img = Image.new("RGB", (w, h), base_color)
    draw = ImageDraw.Draw(img)

    # Main vein
    cx = w // 2
    for x in range(cx - 3, cx + 4):
        draw.line([(x, 0), (x, h)], fill=vein_color, width=1)

    # Secondary veins
    for i in range(1, 10):
        y = int(h * i / 10)
        angle = 35
        length = int(w * 0.35)
        for side in [-1, 1]:
            ex = int(cx + side * length * math.cos(math.radians(angle)))
            ey = int(y - length * math.sin(math.radians(angle)))
            draw.line([(cx, y), (ex, ey)], fill=vein_color, width=1)

    # Leaf outline (ellipse mask)
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([w*0.05, h*0.02, w*0.95, h*0.98], fill=255)
    img_arr = img.copy()
    # Apply green background outside ellipse → dark edge
    bg = Image.new("RGB", (w, h), (20, 60, 20))
    img_arr.paste(bg, mask=ImageOps_invert(mask))

    return img_arr, mask

def ImageOps_invert(mask):
    from PIL import ImageOps
    return ImageOps.invert(mask)

# ─────────────────────────────────────────────────────────────────────────────
# IMAGE A: Potato Early Blight
# Dark concentric rings (target-board / bull's-eye pattern)
# Yellow halo around lesion — Alternaria solani
# ─────────────────────────────────────────────────────────────────────────────
def make_potato_early_blight(path, w=600, h=500):
    from PIL import ImageOps
    import numpy as np

    # Green leaf base
    base  = (55, 120, 40)
    vein  = (35, 90, 25)
    img   = Image.new("RGB", (w, h), base)
    draw  = ImageDraw.Draw(img)

    # Leaf texture — slight gradient
    for y in range(h):
        ratio = y / h
        r = int(base[0] + ratio * 10)
        g = int(base[1] - ratio * 20)
        b = int(base[2] + ratio * 5)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Veins
    cx = w // 2
    for dx in range(-2, 3):
        draw.line([(cx+dx, 20), (cx+dx, h-20)], fill=vein, width=1)
    for i in range(1, 9):
        y = int(h * i / 9)
        for side, angle in [(-1, 40), (1, 40)]:
            llen = int(w * 0.28)
            ex = cx + side * int(llen * math.cos(math.radians(angle)))
            ey = y - int(llen * math.sin(math.radians(angle)))
            draw.line([(cx, y), (ex, ey)], fill=vein, width=1)

    # ── Lesions: 3 target-board spots ────────────────────────────────────
    lesion_centers = [(w//3, h//3), (2*w//3, h//2), (w//2, 2*h//3)]
    lesion_radii   = [55, 45, 40]

    for (lx, ly), lr in zip(lesion_centers, lesion_radii):
        # Yellow halo
        draw.ellipse([lx-lr-18, ly-lr-18, lx+lr+18, ly+lr+18],
                     fill=(210, 190, 30), outline=None)
        # Concentric dark-brown rings (target board)
        rings = 5
        for r_i in range(rings, 0, -1):
            frac = r_i / rings
            rr   = int(lr * frac)
            # Alternate dark brown and medium brown
            if r_i % 2 == 0:
                col = (80, 40, 10)   # dark ring
            else:
                col = (140, 80, 30)  # lighter ring
            draw.ellipse([lx-rr, ly-rr, lx+rr, ly+rr], fill=col)
        # Dark centre
        draw.ellipse([lx-8, ly-8, lx+8, ly+8], fill=(30, 10, 5))

    # Leaf ellipse mask
    mask = Image.new("L", (w, h), 0)
    md   = ImageDraw.Draw(mask)
    md.ellipse([w*0.04, h*0.03, w*0.96, h*0.97], fill=255)
    dark_bg = Image.new("RGB", (w, h), (15, 35, 10))
    img.paste(dark_bg, mask=ImageOps.invert(mask))

    img = noise(img, 12)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    img.save(path, quality=95)
    print(f"  ✅  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# IMAGE B: Apple Black Rot
# Purple-brown circular lesions with dark border — Botryosphaeria obtusa
# ─────────────────────────────────────────────────────────────────────────────
def make_apple_black_rot(path, w=620, h=520):
    from PIL import ImageOps
    import numpy as np

    base = (50, 130, 45)
    vein = (30, 95, 28)
    img  = Image.new("RGB", (w, h), base)
    draw = ImageDraw.Draw(img)

    # Leaf gradient
    for y in range(h):
        g = int(base[1] - (y/h)*15)
        r = int(base[0] + (y/h)*5)
        draw.line([(0, y), (w, y)], fill=(r, g, base[2]))

    # Veins
    cx = w // 2
    for dx in range(-2, 3):
        draw.line([(cx+dx, 15), (cx+dx, h-15)], fill=vein, width=1)
    for i in range(1, 10):
        y = int(h * i / 10)
        for side in [-1, 1]:
            llen = int(w * 0.30)
            ex = cx + side * int(llen * math.cos(math.radians(38)))
            ey = y - int(llen * math.sin(math.radians(38)))
            draw.line([(cx, y), (ex, ey)], fill=vein, width=1)

    # ── Lesions: purple-brown circular spots with dark border ─────────────
    spots = [
        (w//3,     h//3,     60),
        (2*w//3,   h*2//5,   48),
        (w//2,     2*h//3,   42),
        (w//4,     2*h//3,   30),
    ]

    for (sx, sy, sr) in spots:
        # Outer dark border
        draw.ellipse([sx-sr-6, sy-sr-6, sx+sr+6, sy+sr+6],
                     fill=(25, 8, 15), outline=None)
        # Purple-brown fill
        draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr],
                     fill=(110, 35, 60))
        # Inner reddish-brown gradient (fake)
        for layer in range(5):
            frac = layer / 5
            rr   = int(sr * (1 - frac * 0.5))
            col  = (int(130 - layer*12), int(40 + layer*5), int(50 + layer*5))
            draw.ellipse([sx-rr, sy-rr, sx+rr, sy+rr], fill=col)
        # Dark necrotic centre
        draw.ellipse([sx-10, sy-10, sx+10, sy+10], fill=(15, 5, 8))

    # Leaf ellipse mask
    mask = Image.new("L", (w, h), 0)
    md   = ImageDraw.Draw(mask)
    md.ellipse([w*0.04, h*0.03, w*0.96, h*0.97], fill=255)
    dark_bg = Image.new("RGB", (w, h), (10, 30, 8))
    img.paste(dark_bg, mask=ImageOps.invert(mask))

    img = noise(img, 10)
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    img.save(path, quality=95)
    print(f"  ✅  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# IMAGE C: Tomato Late Blight (for completeness — dark water-soaked lesions)
# Already exists but regenerate a fresh one so all 3 match the PDF examples
# ─────────────────────────────────────────────────────────────────────────────
def make_tomato_late_blight(path, w=580, h=500):
    from PIL import ImageOps
    import numpy as np

    base = (48, 125, 42)
    vein = (28, 88, 25)
    img  = Image.new("RGB", (w, h), base)
    draw = ImageDraw.Draw(img)

    for y in range(h):
        g = int(base[1] - (y/h)*12)
        draw.line([(0, y), (w, y)], fill=(base[0], g, base[2]))

    cx = w // 2
    for dx in range(-2, 3):
        draw.line([(cx+dx, 15), (cx+dx, h-15)], fill=vein, width=1)
    for i in range(1, 9):
        y = int(h * i / 9)
        for side in [-1, 1]:
            llen = int(w * 0.29)
            ex = cx + side * int(llen * math.cos(math.radians(36)))
            ey = y - int(llen * math.sin(math.radians(36)))
            draw.line([(cx, y), (ex, ey)], fill=vein, width=1)

    # Dark water-soaked blotches — irregular shapes
    blotches = [
        (w//3,   h//3,   70, 55),
        (2*w//3, h//2,   55, 45),
        (w//2,   2*h//3, 60, 40),
        (w//4,   h//2,   40, 30),
    ]
    for (bx, by, bw, bh) in blotches:
        # Dark brown-black irregular patch
        pts = []
        num = 12
        for k in range(num):
            angle = 2 * math.pi * k / num
            jitter_r = random.uniform(0.7, 1.0)
            jitter_a = angle + random.uniform(-0.2, 0.2)
            px = bx + int(bw * jitter_r * math.cos(jitter_a))
            py = by + int(bh * jitter_r * math.sin(jitter_a))
            pts.append((px, py))
        draw.polygon(pts, fill=(35, 18, 10))
        # White-grey water-soaked margin
        pts2 = []
        for k in range(num):
            angle = 2 * math.pi * k / num
            px = bx + int((bw + 10) * math.cos(angle))
            py = by + int((bh + 8) * math.sin(angle))
            pts2.append((px, py))
        # Draw margin as outline
        for k in range(len(pts2)):
            x1, y1 = pts2[k]
            x2, y2 = pts2[(k+1) % len(pts2)]
            draw.line([(x1,y1),(x2,y2)], fill=(190, 200, 180), width=3)

    # Leaf ellipse mask
    mask = Image.new("L", (w, h), 0)
    md   = ImageDraw.Draw(mask)
    md.ellipse([w*0.04, h*0.03, w*0.96, h*0.97], fill=255)
    dark_bg = Image.new("RGB", (w, h), (10, 28, 8))
    img.paste(dark_bg, mask=ImageOps.invert(mask))

    img = noise(img, 14)
    img = img.filter(ImageFilter.GaussianBlur(0.7))
    img.save(path, quality=95)
    print(f"  ✅  Saved: {path}")


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🌿  Generating PDF example images...\n")

    make_tomato_late_blight(
        os.path.join(OUT, "EX1_Tomato_Late_Blight_PDFExample.jpg"))

    make_potato_early_blight(
        os.path.join(OUT, "EX2_Potato_Early_Blight_PDFExample.jpg"))

    make_apple_black_rot(
        os.path.join(OUT, "EX3_Apple_Black_Rot_PDFExample.jpg"))

    print("\n✅  All 3 PDF example images generated in DEMO_IMAGES/\n")
    print("  EX1_Tomato_Late_Blight_PDFExample.jpg  — Example 1 from PDF")
    print("  EX2_Potato_Early_Blight_PDFExample.jpg — Example 2 from PDF")
    print("  EX3_Apple_Black_Rot_PDFExample.jpg     — Example 3 from PDF")
    print()
