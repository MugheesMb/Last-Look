
import io

from PIL import Image, UnidentifiedImageError

try:
    # iPhone/Mac photos are often HEIC by default, which Pillow can't read
    # without this plugin. Registering it here makes Image.open() transparently
    # handle .heic files too, not just JPEG/PNG.
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass

TOP_FRACTION = 0.55   # keep the top 55% of the image height (where the face sits)
WIDTH_FRACTION = 0.65  # keep the center 65% of the image width
MIN_DIMENSION = 512   # upscale the crop if either side ends up smaller than this

# Padding around a REAL detected face box (as a multiple of the face's own
# width/height) — generous enough to include some forehead/chin/hair
# context, since Skin Analysis needs a face, not just a tight eyes-to-mouth
# crop, but tight enough to keep the face a large fraction of the frame.
FACE_PAD_SIDES = 0.6
FACE_PAD_TOP = 0.8
FACE_PAD_BOTTOM = 0.6


class UnsupportedImageError(ValueError):
    """Raised when the uploaded bytes aren't a readable image format."""


def crop_for_face(image_bytes: bytes, face_box: dict | None = None) -> bytes:
    """Crops to a face-focused region for Skin Analysis.

    If a real detected face_box is provided (x, y, w, h as fractions of the
    full image, from face-api.js running client-side during camera capture),
    crops precisely around THAT — grounded in an actual detection rather
    than a blind heuristic. This replaced the original top-55%/center-65%
    guess after it kept producing "face too small" rejections whenever a
    person's face sat somewhere other than dead-center-top of the frame
    (e.g. more chest visible, slightly off-center). Falls back to the old
    heuristic when no detection is available (upload flow has no live
    detection to draw from).
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError:
        raise UnsupportedImageError(
            "Couldn't read this file as an image. Try a JPEG or PNG "
            "(if this came from an iPhone/Mac, it may be HEIC — try "
            "re-saving or re-exporting as JPEG first)."
        )
    width, height = img.size

    if face_box:
        fx, fy, fw, fh = face_box["x"], face_box["y"], face_box["w"], face_box["h"]
        # Convert fractions to pixels, then pad generously around the
        # detected box rather than cropping exactly to it.
        face_left = fx * width
        face_top = fy * height
        face_right = (fx + fw) * width
        face_bottom = (fy + fh) * height
        face_w_px = face_right - face_left
        face_h_px = face_bottom - face_top

        left = max(0, face_left - face_w_px * FACE_PAD_SIDES)
        right = min(width, face_right + face_w_px * FACE_PAD_SIDES)
        top = max(0, face_top - face_h_px * FACE_PAD_TOP)
        bottom = min(height, face_bottom + face_h_px * FACE_PAD_BOTTOM)
        left, top, right, bottom = int(left), int(top), int(right), int(bottom)
    else:
        crop_height = int(height * TOP_FRACTION)
        crop_width = int(width * WIDTH_FRACTION)
        left = (width - crop_width) // 2
        right = left + crop_width
        top = 0
        bottom = crop_height

    cropped = img.crop((left, top, right, bottom))

    # Cropping shrinks an already-modest webcam-resolution photo well below
    # whatever minimum pixel size YouCam's API requires (hit in testing:
    # error_below_min_image_size). Scale back up if needed, preserving
    # aspect ratio — upscaling a face crop loses some sharpness but that's
    # a much smaller problem than the request being rejected outright.
    cropped_width, cropped_height = cropped.size
    smaller_side = min(cropped_width, cropped_height)
    if smaller_side < MIN_DIMENSION:
        scale = MIN_DIMENSION / smaller_side
        new_size = (round(cropped_width * scale), round(cropped_height * scale))
        cropped = cropped.resize(new_size, Image.LANCZOS)

    out = io.BytesIO()
    cropped.save(out, format="JPEG", quality=92)
    return out.getvalue()


def estimate_skin_tone(face_crop_bytes: bytes) -> dict:
    """Samples actual pixel color from the face crop to estimate undertone
    and depth — grounded in the real photo instead of an LLM guessing blind.

    YouCam's Skin Analysis API doesn't return any tone/undertone data (only
    concern scores — confirmed via live testing), so without this, every
    result depended entirely on the LLM inventing an undertone with zero
    real signal to differentiate one person's photo from another's, which
    is exactly why the color season kept coming back the same regardless
    of who was in the photo.

    This is a simple heuristic (average color of a center-face sample
    region, not real skin-tone science), but it's grounded in the actual
    pixels of the actual photo, so it varies per person the way it should.
    """
    img = Image.open(io.BytesIO(face_crop_bytes)).convert("RGB")
    width, height = img.size

    # Sample a small box in the center-lower area of the crop — cheek/nose
    # region on a typical face-focused crop, avoiding hair/eyes/background.
    box_w, box_h = int(width * 0.25), int(height * 0.15)
    left = (width - box_w) // 2
    top = int(height * 0.55)
    sample = img.crop((left, top, left + box_w, top + box_h))

    pixels = list(sample.getdata())
    r = sum(p[0] for p in pixels) / len(pixels)
    g = sum(p[1] for p in pixels) / len(pixels)
    b = sum(p[2] for p in pixels) / len(pixels)

    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    if luminance > 175:
        depth = "light"
    elif luminance > 110:
        depth = "medium"
    else:
        depth = "deep"

    # Warm undertones skew red/yellow (higher R relative to B); cool
    # undertones skew pink/blue (R and B closer together, or B higher).
    r_b_gap = r - b
    if r_b_gap > 25:
        undertone = "warm"
    elif r_b_gap < 10:
        undertone = "cool"
    else:
        undertone = "neutral"

    return {"undertone": undertone, "depth": depth}
