#!/usr/bin/env python3
import math
import struct
import zlib
from pathlib import Path


def clamp01(value):
    return max(0.0, min(1.0, value))


def blend(dst, src):
    dr, dg, db, da = dst
    sr, sg, sb, sa = src

    sa_f = sa / 255.0
    da_f = da / 255.0
    out_a = sa_f + da_f * (1.0 - sa_f)
    if out_a <= 0.0:
        return (0, 0, 0, 0)

    out_r = (sr * sa_f + dr * da_f * (1.0 - sa_f)) / out_a
    out_g = (sg * sa_f + dg * da_f * (1.0 - sa_f)) / out_a
    out_b = (sb * sa_f + db * da_f * (1.0 - sa_f)) / out_a
    return (int(round(out_r)), int(round(out_g)), int(round(out_b)), int(round(out_a * 255.0)))


def write_png(path, width, height, pixels):
    def chunk(tag, payload):
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    raw = bytearray()
    for y in range(height):
        raw.append(0)
        row_start = y * width
        for x in range(width):
            r, g, b, a = pixels[row_start + x]
            raw.extend((r, g, b, a))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(bytes(raw), level=9)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    path.write_bytes(png)


def draw_disc(pixels, width, height, cx, cy, radius, color):
    r, g, b, a = color
    x0 = max(0, int(math.floor(cx - radius - 1.0)))
    x1 = min(width - 1, int(math.ceil(cx + radius + 1.0)))
    y0 = max(0, int(math.floor(cy - radius - 1.0)))
    y1 = min(height - 1, int(math.ceil(cy + radius + 1.0)))

    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            dx = (x + 0.5) - cx
            dy = (y + 0.5) - cy
            dist = math.hypot(dx, dy)
            cover = clamp01(radius + 0.55 - dist)
            if cover <= 0.0:
                continue
            src = (r, g, b, int(round(a * cover)))
            idx = y * width + x
            pixels[idx] = blend(pixels[idx], src)


def erase_disc(pixels, width, height, cx, cy, radius):
    x0 = max(0, int(math.floor(cx - radius - 1.0)))
    x1 = min(width - 1, int(math.ceil(cx + radius + 1.0)))
    y0 = max(0, int(math.floor(cy - radius - 1.0)))
    y1 = min(height - 1, int(math.ceil(cy + radius + 1.0)))

    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            dx = (x + 0.5) - cx
            dy = (y + 0.5) - cy
            dist = math.hypot(dx, dy)
            cover = clamp01(radius + 0.55 - dist)
            if cover <= 0.0:
                continue
            idx = y * width + x
            pr, pg, pb, pa = pixels[idx]
            alpha_scale = 1.0 - cover
            pixels[idx] = (pr, pg, pb, int(round(pa * alpha_scale)))


def _distance_to_segment(px, py, ax, ay, bx, by):
    vx = bx - ax
    vy = by - ay
    wx = px - ax
    wy = py - ay
    vv = vx * vx + vy * vy
    if vv == 0.0:
        return math.hypot(px - ax, py - ay)
    t = (wx * vx + wy * vy) / vv
    t = max(0.0, min(1.0, t))
    qx = ax + t * vx
    qy = ay + t * vy
    return math.hypot(px - qx, py - qy)


def draw_line_round(pixels, width, height, ax, ay, bx, by, thickness, color):
    r, g, b, a = color
    half = thickness / 2.0
    x0 = max(0, int(math.floor(min(ax, bx) - half - 1.0)))
    x1 = min(width - 1, int(math.ceil(max(ax, bx) + half + 1.0)))
    y0 = max(0, int(math.floor(min(ay, by) - half - 1.0)))
    y1 = min(height - 1, int(math.ceil(max(ay, by) + half + 1.0)))

    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            dist = _distance_to_segment(x + 0.5, y + 0.5, ax, ay, bx, by)
            cover = clamp01(half + 0.55 - dist)
            if cover <= 0.0:
                continue
            src = (r, g, b, int(round(a * cover)))
            idx = y * width + x
            pixels[idx] = blend(pixels[idx], src)


def draw_ring(pixels, width, height, cx, cy, inner_radius, outer_radius, color, mask_alpha_threshold=0):
    x0 = max(0, int(math.floor(cx - outer_radius - 1.0)))
    x1 = min(width - 1, int(math.ceil(cx + outer_radius + 1.0)))
    y0 = max(0, int(math.floor(cy - outer_radius - 1.0)))
    y1 = min(height - 1, int(math.ceil(cy + outer_radius + 1.0)))
    r, g, b, a = color

    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            dx = (x + 0.5) - cx
            dy = (y + 0.5) - cy
            dist = math.hypot(dx, dy)
            outer_cover = clamp01(outer_radius + 0.55 - dist)
            inner_cover = clamp01(inner_radius + 0.55 - dist)
            cover = max(0.0, outer_cover - inner_cover)
            if cover <= 0.0:
                continue
            idx = y * width + x
            if pixels[idx][3] < mask_alpha_threshold:
                continue
            src = (r, g, b, int(round(a * cover)))
            pixels[idx] = blend(pixels[idx], src)


def create_sun_icon(size):
    pixels = [(0, 0, 0, 0)] * (size * size)
    cx = size / 2.0
    cy = size / 2.0
    core = size * 0.23
    ray_inner = core + size * 0.08
    ray_outer = size * 0.47
    ray_width = max(1.2, size * 0.09)

    for i in range(12):
        angle = (math.pi * 2.0 / 12.0) * i
        ax = cx + math.cos(angle) * ray_inner
        ay = cy + math.sin(angle) * ray_inner
        bx = cx + math.cos(angle) * ray_outer
        by = cy + math.sin(angle) * ray_outer
        draw_line_round(pixels, size, size, ax, ay, bx, by, ray_width, (255, 170, 40, 220))

    draw_disc(pixels, size, size, cx, cy, core * 1.45, (255, 130, 20, 110))
    draw_disc(pixels, size, size, cx, cy, core, (255, 215, 60, 255))
    draw_disc(pixels, size, size, cx, cy, core * 0.62, (255, 245, 150, 255))
    return pixels


def create_moon_icon(size):
    pixels = [(0, 0, 0, 0)] * (size * size)
    cx = size / 2.0
    cy = size / 2.0
    outer = size * 0.40
    inner = outer * 0.86
    cut_cx = cx + size * 0.18
    cut_cy = cy - size * 0.03

    draw_disc(pixels, size, size, cx, cy, outer, (35, 35, 35, 250))
    erase_disc(pixels, size, size, cut_cx, cut_cy, inner)
    draw_ring(pixels, size, size, cx, cy, outer - max(1.0, size * 0.07), outer, (255, 255, 255, 245))
    draw_ring(
        pixels,
        size,
        size,
        cut_cx,
        cut_cy,
        inner - max(0.9, size * 0.05),
        inner + max(0.9, size * 0.05),
        (255, 255, 255, 235),
        mask_alpha_threshold=10,
    )
    return pixels


def main():
    root = Path(__file__).resolve().parent.parent
    icons_dir = root / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    for size in (16, 32, 48, 128):
        write_png(icons_dir / f"sun-{size}.png", size, size, create_sun_icon(size))
        write_png(icons_dir / f"moon-{size}.png", size, size, create_moon_icon(size))

    print(f"Generated icons in: {icons_dir}")


if __name__ == "__main__":
    main()
