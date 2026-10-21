"""UV-authored structural height with optional shallow upgraded-color grain.

Features describe apparent material relief, not recovered/measured dimensions.
Paint/glass masks are explicit; color brightness cannot create structural forms.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def mask(size, shape):
    """Rasterize a normalized UV recipe into a floating mask in [0, 1].

    UV endpoints map to the first and last stored pixels. Line width is a
    fraction of the shorter image dimension, rounded to at least one pixel.
    """
    w, h = size
    image = Image.new("L", size)
    draw = ImageDraw.Draw(image)
    points = shape["points"]
    if not points or any(len(p) != 2 or not all(0 <= v <= 1 for v in p) for p in points):
        raise ValueError("Feature coordinates outside normalized UV space")
    xy = [(round(x * (w - 1)), round(y * (h - 1))) for x, y in points]
    width = max(1, round(min(size) * shape.get("width", 0.015)))
    kind = shape["shape"]
    if kind == "rect":
        if len(xy) != 2 or xy[0][0] >= xy[1][0] or xy[0][1] >= xy[1][1]:
            raise ValueError("Invalid feature rectangle")
        draw.rectangle(xy, fill=255)
    elif kind == "line":
        if len(xy) < 2:
            raise ValueError("Feature line requires two points")
        draw.line(xy, fill=255, width=width)
    elif kind == "outline":
        if len(xy) < 3:
            raise ValueError("Feature outline requires polygon")
        draw.line(xy + [xy[0]], fill=255, width=width)
    elif kind == "polygon":
        if len(xy) < 3:
            raise ValueError("Feature polygon requires three points")
        draw.polygon(xy, fill=255)
    else:
        raise ValueError("Unknown structural feature shape: " + kind)
    return np.asarray(image, dtype=float) / 255.0


def smooth(value, sigma=0.8):
    """Apply a separable Gaussian to a 2-D field with replicated edge pixels.

    Sigma is measured in pixels; unlike the world texture filter, this filter
    does not wrap across an object's atlas edges.
    """
    radius = max(1, int(np.ceil(sigma * 3)))
    weights = np.exp(-np.arange(-radius, radius + 1, dtype=float) ** 2 / (2 * sigma * sigma))
    weights /= weights.sum()
    for axis in (0, 1):
        pads = [(0, 0), (0, 0)]
        pads[axis] = (radius, radius)
        padded = np.pad(value, pads, mode="edge")
        value = sum(
            weight * np.take(padded, np.arange(value.shape[axis]) + i, axis=axis)
            for i, weight in enumerate(weights)
        )
    return value


def feature_relief(image, recipe, *, grain_mask=None):
    """Return a normal-map tuple, editable 16-bit height image and slope statistics.

    Authored feature masks supply structure; filtered color contributes only
    optional grain. A boolean grain mask permits grain, while flat regions also
    force the final normals flat. Rows remain in stored image order.
    """
    image = image.convert("RGB")
    w, h = image.size
    if min(w, h) < 8:
        raise ValueError("Feature surface too small")
    gray = image.convert("L")
    fine = np.asarray(gray.filter(ImageFilter.GaussianBlur(0.6)), dtype=float) / 255.0
    broad = np.asarray(gray.filter(ImageFilter.GaussianBlur(2.5)), dtype=float) / 255.0
    micro = (fine - broad) * recipe.get("micro_gain", 0.04)
    flat = np.zeros((h, w), dtype=bool)
    for spec in recipe.get("flat_regions", []):
        flat |= mask(image.size, spec) > 0
    suppress = flat.copy()
    if grain_mask is not None:
        permitted = np.asarray(grain_mask)
        if permitted.shape != (h, w) or permitted.dtype != np.bool_:
            raise ValueError("Grain mask must match the surface dimensions")
        suppress |= ~permitted
    for spec in recipe.get("paint_boundaries", []):
        # Dilate the mask before differentiation so painted color transitions
        # cannot leak back into the height field through a filter footprint.
        image_mask = Image.fromarray(np.rint(mask(image.size, spec) * 255).astype("uint8"))
        suppress |= np.asarray(image_mask.filter(ImageFilter.MaxFilter(9))) > 0
    micro[suppress] = 0
    height_field = micro.copy()
    for spec in recipe["features"]:
        amount = float(spec["height"])
        if not np.isfinite(amount) or abs(amount) > 0.25:
            raise ValueError("Invalid feature height")
        height_field += mask(image.size, spec) * amount
    height_field = smooth(height_field)
    # Convert per-pixel derivatives to the recipe's normalized surface scale.
    # Retain stored-V orientation and encode the negative height derivatives.
    dy, dx = np.gradient(height_field)
    dx *= w * recipe["depth_ratio"]
    dy *= h * recipe["depth_ratio"]
    slopes = np.sqrt(dx * dx + dy * dy)
    slope_scale = np.minimum(1.0, recipe["slope_limit"] / np.maximum(slopes, 1e-12))
    unit_normals = np.stack((-dx * slope_scale, -dy * slope_scale, np.ones_like(dx)), axis=-1)
    unit_normals /= np.linalg.norm(unit_normals, axis=-1, keepdims=True)
    rgba = np.full((h, w, 4), 255, dtype="uint8")
    rgba[:, :, :3] = np.rint(np.clip(unit_normals * 0.5 + 0.5, 0, 1) * 255).astype("uint8")
    rgba[flat, :3] = [128, 128, 255]
    rgba[:2, :, :3] = rgba[-2:, :, :3] = [128, 128, 255]
    rgba[:, :2, :3] = rgba[:, -2:, :3] = [128, 128, 255]
    stats = dict(
        median_slope=float(np.median(slopes * slope_scale)),
        p95_slope=float(np.percentile(slopes * slope_scale, 95)),
        max_slope=float((slopes * slope_scale).max()),
        clipped_fraction=float(np.mean(slopes > recipe["slope_limit"])),
        flat_pixels=int(flat.sum()),
        features=len(recipe["features"]),
    )
    # Float height remains the source of the derivatives; 16-bit export is an
    # editable data artifact, avoiding 8-bit quantization of shallow metal grain.
    height = Image.fromarray(np.rint(np.clip(0.5 + height_field, 0, 1) * 65535).astype("uint16"))
    return (w, h, rgba.tobytes()), height, stats
