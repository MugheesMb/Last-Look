
import colorsys
import io

import httpx
from PIL import Image


async def fetch_image_bytes(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


def dominant_color(image_bytes: bytes) -> str:
    """Returns the dominant color of an image as a hex string."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((150, 150))  # downscale for speed
    quantized = img.quantize(colors=8, method=Image.MEDIANCUT)
    palette = quantized.getpalette()
    color_counts = quantized.getcolors()
    color_counts.sort(reverse=True, key=lambda c: c[0])
    top_index = color_counts[0][1]
    r, g, b = palette[top_index * 3 : top_index * 3 + 3]
    return f"#{r:02X}{g:02X}{b:02X}"


def _is_skin_tone(r: int, g: int, b: int) -> bool:
    """A standard, widely-used RGB skin-detection heuristic (Peer et al.).
    Not perfect — very tan/camel fabric can still get misclassified, since
    it's genuinely close to skin in raw RGB terms — but it correctly
    excludes the neck/chest/face pixels that were dominating the garment
    color reading before."""
    return (
        r > 95
        and g > 40
        and b > 20
        and (max(r, g, b) - min(r, g, b)) > 15
        and abs(r - g) > 15
        and r > g
        and r > b
    )


def _is_background_like(r: int, g: int, b: int) -> bool:
    """Plain studio background (near-white / light gray) — bright and low
    saturation. This was the actual bug behind a black top reading as
    white: excluding skin alone still left the background as the next
    most common thing in the crop for a garment that barely covers any
    of the frame, and nothing was filtering that out."""
    _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return v > 0.85 and s < 0.12


def garment_dominant_color(image_bytes: bytes) -> str:
    """Dominant color of the GARMENT specifically, not the whole rendered
    photo. Three problems compounded here, found and fixed iteratively:

    1. dominant_color() alone scans the whole image — mostly face/hair/
       background on a VTO render — so a thin-strap or low-coverage
       garment loses to whatever's biggest in the frame.
    2. Cropping to the lower-center region alone wasn't enough: a wide
       neckline or thin straps mean that region is STILL mostly visible
       neck/chest skin, not fabric.
    3. Excluding skin tone alone still wasn't enough: once skin is
       excluded, the plain white STUDIO BACKGROUND becomes the next most
       common thing in a thin-strap garment's crop, and that was never
       being filtered out either.

    Fix: crop to the likely garment region, then walk color clusters by
    frequency and skip any that look like skin OR plain background,
    returning the first genuinely-garment-colored cluster."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    width, height = img.size

    crop_top = int(height * 0.55)
    crop_left = int(width * 0.2)
    crop_right = int(width * 0.8)
    garment_region = img.crop((crop_left, crop_top, crop_right, height))

    garment_region = garment_region.resize((100, 100))
    quantized = garment_region.quantize(colors=10, method=Image.MEDIANCUT)
    palette = quantized.getpalette()
    color_counts = quantized.getcolors()
    color_counts.sort(reverse=True, key=lambda c: c[0])

    for _count, index in color_counts:
        r, g, b = palette[index * 3 : index * 3 + 3]
        if not _is_skin_tone(r, g, b) and not _is_background_like(r, g, b):
            return f"#{r:02X}{g:02X}{b:02X}"

    # Every cluster looked like skin or background — fall back to the top
    # cluster rather than returning nothing.
    r, g, b = palette[color_counts[0][1] * 3 : color_counts[0][1] * 3 + 3]
    return f"#{r:02X}{g:02X}{b:02X}"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore


def color_distance(hex_a: str, hex_b: str) -> float:
    """Weighted Euclidean RGB distance, roughly perceptual (redmean approximation)."""
    r1, g1, b1 = _hex_to_rgb(hex_a)
    r2, g2, b2 = _hex_to_rgb(hex_b)
    r_mean = (r1 + r2) / 2
    dr, dg, db = r1 - r2, g1 - g2, b1 - b2
    weight_r = 2 + r_mean / 256
    weight_g = 4.0
    weight_b = 2 + (255 - r_mean) / 256
    return (weight_r * dr**2 + weight_g * dg**2 + weight_b * db**2) ** 0.5


def best_palette_match(hex_color: str, palette: list[str]) -> tuple[str, float]:
    """Returns (closest_palette_color, distance) for the given color."""
    scored = [(p, color_distance(hex_color, p)) for p in palette]
    scored.sort(key=lambda x: x[1])
    return scored[0]


# Hue-based color naming (HSV), not RGB-swatch matching. RGB distance to a
# small fixed swatch list was the actual bug behind a visibly-green dress
# getting named "gray" for its shop search: a muted/desaturated fabric
# green under studio lighting can end up numerically closer to a gray
# swatch than any green swatch in raw RGB terms, even though a person
# looking at it would call it green without hesitation. Hue is far more
# stable than raw RGB under lighting/desaturation changes, which is what
# we actually need for naming a color category, not measuring exact match.
def nearest_color_name(hex_color: str) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h_deg = h * 360

    if s < 0.15:
        if v > 0.85:
            return "white"
        if v < 0.25:
            return "black"
        return "gray"

    if v < 0.35:
        if h_deg < 20 or h_deg >= 340:
            return "burgundy"
        if 20 <= h_deg < 60:
            return "brown"
        if 60 <= h_deg < 170:
            return "dark green"
        return "navy"

    if h_deg < 15 or h_deg >= 345:
        return "red"
    if 15 <= h_deg < 45:
        return "orange"
    if 45 <= h_deg < 65:
        return "gold"
    if 65 <= h_deg < 170:
        return "green"
    if 170 <= h_deg < 200:
        return "teal"
    if 200 <= h_deg < 250:
        return "blue"
    if 250 <= h_deg < 290:
        return "purple"
    if 290 <= h_deg < 345:
        return "pink"
    return "gray"
