#!/usr/bin/env python3
"""Generate tray icons as true-color RGBA PNGs."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
SIZE = 128
PAD = 8


def _base(color: tuple[int, int, int, int]) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((PAD, PAD, SIZE - PAD - 1, SIZE - PAD - 1), fill=color)
    return img, draw


def connected() -> Image.Image:
    img, draw = _base((34, 197, 94, 255))  # green-500
    # Thick white checkmark
    pts = [(38, 66), (54, 84), (92, 44)]
    draw.line(pts, fill=(255, 255, 255, 255), width=14, joint="curve")
    return img


def disconnected() -> Image.Image:
    img, draw = _base((239, 68, 68, 255))  # red-500
    draw.line((42, 42, 86, 86), fill=(255, 255, 255, 255), width=14)
    draw.line((86, 42, 42, 86), fill=(255, 255, 255, 255), width=14)
    return img


def unknown() -> Image.Image:
    img, draw = _base((148, 163, 184, 255))  # slate-400
    for cx, alpha in ((40, 255), (64, 190), (88, 115)):
        r = 9
        draw.ellipse((cx - r, 64 - r, cx + r, 64 + r), fill=(255, 255, 255, alpha))
    return img


def main() -> None:
    mapping = {
        "shecan-connected.png": connected(),
        "shecan-disconnected.png": disconnected(),
        "shecan-unknown.png": unknown(),
    }
    for name, img in mapping.items():
        path = OUT / name
        img.save(path, format="PNG")
        # Also export panel-sized copy for crisp tray rendering
        small = img.resize((32, 32), Image.Resampling.LANCZOS)
        small.save(path, format="PNG")
        print(f"wrote {path} mode={small.mode}")


if __name__ == "__main__":
    main()
