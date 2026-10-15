"""Render the software-only demo preview for Computational Respiration.

Requires Python 3, Pillow, and ffmpeg on PATH. No hardware is needed.
"""
from __future__ import annotations
import csv
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
FPS = 12
SECONDS = 30
W, H = 960, 540


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


def target_at(t: float) -> float:
    if t < 5: return 20.0
    if t < 10: return 55.0
    if t < 15: return 90.0
    ramp = (t - 15) % 15.0
    x = ramp / 7.5 if ramp <= 7.5 else 2.0 - ramp / 7.5
    return 20.0 + 70.0 * x


def simulate():
    heat = 20.0
    phase = 0.0
    rows = []
    for i in range(SECONDS * FPS):
        t = i / FPS
        target = target_at(t)
        dt = 1 / FPS
        heat += (target - heat) * (1 - math.exp(-2.8 * dt))
        x = heat / 100
        base = lerp(0.25, 0.90, x)
        period = lerp(6.0, 1.5, x)
        min_breath = lerp(0.85, 0.65, x)
        phase = (phase + dt / period) % 1.0
        wave = (math.sin(2 * math.pi * phase) + 1) / 2
        brightness = base * (min_breath + (1 - min_breath) * wave)
        rgb = (round(255 * brightness), round(lerp(190, 70, x) * brightness), round(lerp(120, 20, x) * brightness))
        rows.append((t, target, heat, brightness, *rgb))
    return rows


def font(size: int):
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try: return ImageFont.truetype(name, size)
        except OSError: pass
    return ImageFont.load_default()


def make_frame(row, rows):
    t, target, heat, brightness, r, g, b = row
    image = Image.new("RGB", (W, H), (13, 16, 23))
    d = ImageDraw.Draw(image)
    title = font(28); label = font(18); big = font(48); small = font(15)
    d.text((40, 28), "COMPUTATIONAL RESPIRATION", fill=(236, 240, 245), font=title)
    d.text((40, 70), "software validation · smoothed response", fill=(137, 148, 164), font=small)
    # Lamp
    cx, cy, rad = 220, 255, 118
    glow = max(r, g, b)
    for rr in range(rad + 55, rad, -3):
        a = (rad + 55 - rr) / 55
        col = tuple(int(13 + c * a * 0.22) for c in (r, g, b))
        d.ellipse((cx-rr, cy-rr, cx+rr, cy+rr), fill=col)
    d.ellipse((cx-rad, cy-rad, cx+rad, cy+rad), fill=(r, g, b), outline=(255, 255, 255), width=3)
    d.text((cx-52, cy-24), f"{heat:4.0f}%", fill=(255, 255, 255), font=big)
    d.text((cx-54, cy+38), "LOAD", fill=(245, 245, 245), font=label)
    # State label
    state = "LOW" if target < 35 else "MEDIUM" if target < 75 else "HIGH"
    d.text((410, 126), state, fill=(255, 180, 80), font=big)
    d.text((410, 188), f"target {target:4.0f}%    smoothed {heat:4.0f}%", fill=(210, 219, 230), font=label)
    d.text((410, 224), f"RGB {r:03d} {g:03d} {b:03d}    brightness {brightness:.2f}", fill=(160, 174, 190), font=label)
    # Trace
    x0, y0, x1, y1 = 410, 300, 910, 470
    d.rectangle((x0, y0, x1, y1), outline=(62, 72, 88), width=2)
    d.text((x0, y0-30), "thermal load trace", fill=(160, 174, 190), font=label)
    visible = [x for x in rows if x[0] <= t]
    if len(visible) > 1:
        def pts(idx): return [(x0 + v[0] / SECONDS * (x1-x0), y1 - v[idx] / 100 * (y1-y0)) for v in visible]
        d.line(pts(1), fill=(255, 178, 70), width=3)
        d.line(pts(2), fill=(102, 210, 190), width=3)
    d.text((x0, y1+14), "orange target", fill=(255, 178, 70), font=small)
    d.text((x0+150, y1+14), "teal smoothed", fill=(102, 210, 190), font=small)
    d.text((W-120, 28), f"{t:04.1f}s", fill=(160, 174, 190), font=label)
    return image


def main():
    DOCS.mkdir(exist_ok=True)
    rows = simulate()
    with (DOCS / "demo-trace.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "target_heat", "smoothed_heat", "brightness", "r", "g", "b"])
        writer.writerows(rows)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required to render the MP4 preview")
    with tempfile.TemporaryDirectory() as temp:
        temp_path = Path(temp)
        for i, row in enumerate(rows):
            make_frame(row, rows).save(temp_path / f"frame_{i:05d}.png")
        output = DOCS / "continuous-load-demo.mp4"
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(temp_path / "frame_%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24", str(output)], check=True)
    print(f"wrote {DOCS / 'demo-trace.csv'}")
    print(f"wrote {DOCS / 'continuous-load-demo.mp4'}")


if __name__ == "__main__":
    main()

