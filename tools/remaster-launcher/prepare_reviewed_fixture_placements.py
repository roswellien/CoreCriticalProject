"""Stage user-reviewed UV light placements and technical diagrams; no live edits.

Read upgraded source pixels and coverage. Output masks are proposed emission
regions, not replacement albedo or proof of runtime UV/world placement.
"""

from pathlib import Path
import argparse, collections, csv, hashlib, json, re, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
PALETTE = {
    "red": (1, 0.025, 0.015),
    "green": (0.06, 1, 0.12),
    "blue": (0.05, 0.25, 1),
    "purple": (0.65, 0.10, 1),
    "yellow": (1, 0.82, 0.12),
    "warm_white": (1, 0.91, 0.67),
    "white": (1, 1, 1),
    "teal": (0.04, 1, 0.83),
    "orange": (1, 0.28, 0.015),
}


def source_image(row, audit):
    src = row["sources"][0]
    if row["id"].startswith("M"):
        # The native replacement archive discards PNG alpha (RGB565 material).
        # Some source alpha channels encode material data rather than coverage.
        image = Image.open(src["path"]).convert("RGB")
        if hashlib.sha256(image.tobytes()).hexdigest() != row["pixel_sha256"]:
            raise ValueError("Reviewed model pixels changed: " + row["id"])
        return image.convert("RGBA")
    bank = next(p["path"] for p in audit["bank_pins"] if p["bank"] == src["bank"])
    with open(bank, "rb") as f:
        f.seek(src["offset"])
        flags, w, h, _, _, _ = struct.unpack("<IHHIHH", f.read(16))
        raw = f.read(w * h * 2)
        words = np.frombuffer(raw, "<u2").reshape(h, w).astype("uint32")
        coverage = f.read(w * h) if (flags & ~96) == 11 else b""
        if hashlib.sha256(raw + coverage).hexdigest() != row["pixel_sha256"]:
            raise ValueError("Reviewed bank pixels changed: " + row["id"])
        alpha = (
            np.frombuffer(coverage, "uint8").reshape(h, w)
            if coverage
            else (
                np.where(words != 0, 255, 0).astype("uint8")
                if (flags & ~96) == 3
                else np.full((h, w), 255, "uint8")
            )
        )
    rgb = np.stack(
        (
            (words >> 11) * 255 // 31,
            ((words >> 5) & 63) * 255 // 63,
            (words & 31) * 255 // 31,
            alpha,
        ),
        axis=-1,
    ).astype("uint8")
    return Image.fromarray(rgb)


def role(row):
    names = " ".join(row["names"]).lower()
    if row["id"].startswith("M"):
        return "model UV lights"
    if re.search(r"hud_|lab_|cpit", names):
        return "screen/cockpit glow"
    if "northlite" in names:
        return "atmospheric glow"
    if "rokt" in names:
        return "moving effect lighting"
    return "world UV lights"


def components(mask):
    # Close tiny gaps within a single indicator; retain separate lamps.
    mask = (
        np.asarray(
            Image.fromarray((mask * 255).astype("uint8"))
            .filter(ImageFilter.MaxFilter(3))
            .filter(ImageFilter.MinFilter(3))
        )
        > 0
    )
    seen = np.zeros(mask.shape, bool)
    h, w = mask.shape
    out = []
    for yy, xx in zip(*np.nonzero(mask)):
        if seen[yy, xx]:
            continue
        todo = [(int(xx), int(yy))]
        seen[yy, xx] = True
        xs = []
        ys = []
        while todo:
            x, y = todo.pop()
            xs.append(x)
            ys.append(y)
            for u, v in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
                if 0 <= u < w and 0 <= v < h and mask[v, u] and not seen[v, u]:
                    seen[v, u] = True
                    todo.append((u, v))
        if len(xs) >= 3:
            out.append(
                (
                    len(xs),
                    min(xs),
                    min(ys),
                    max(xs) + 1,
                    max(ys) + 1,
                    float(np.mean(xs)),
                    float(np.mean(ys)),
                )
            )
    return sorted(out, reverse=True)


def placements(image, colors, rule, page, id_, names):
    im = image.copy()
    im.thumbnail((512, 512))
    a = np.asarray(im)
    rgb = a[:, :, :3].astype(float) / 255
    alpha = a[:, :, 3] > 32
    alpha = a[:, :, 3] > 0
    h, w = alpha.shape
    y, x = np.mgrid[:h, :w]
    xx = (x + 0.5) / w
    yy = (y + 0.5) / h
    rad = np.sqrt((xx - 0.5) ** 2 + (yy - 0.5) ** 2)
    r, g, b = np.moveaxis(rgb, -1, 0)
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
    emission = np.zeros((*alpha.shape, 4), "uint8")
    points = []
    inferred = []
    for index, color in enumerate(colors):
        tint = PALETTE.get(color)
        if color == "texture":
            bright = alpha & (lum >= np.quantile(lum[alpha], 0.88) if alpha.any() else False)
            tint = (
                tuple(np.maximum(0.02, np.mean(rgb[bright], axis=0))) if bright.any() else (1, 1, 1)
            )
            mask = bright
        else:
            masks = {
                "red": (r > 0.42) & (r > g * 1.45) & (r > b * 1.35),
                "green": (g > 0.28) & (g > r * 1.25) & (g > b * 1.12),
                "blue": (b > 0.35) & (b > r + 0.025) & (b > g + 0.008),
                "purple": (r > g + 0.012) & (b > g + 0.012) & (b > 0.35),
                "yellow": (r > 0.4) & (g > 0.3) & (r > b * 1.14) & (g > b * 1.05),
                "warm_white": (r > 0.52) & (g > 0.42) & (r >= b * 0.95) & (g > b * 0.8),
                "white": np.minimum.reduce([r, g, b]) > 0.6,
                "teal": (g > 0.35) & (b > 0.3) & (g > r * 1.12) & (b > r * 1.12),
                "orange": (r > 0.45) & (g > 0.15) & (r > g * 1.35) & (g > b * 1.15),
            }
            mask = masks[color]
        mask = mask & alpha
        single_panel = id_ in ("T2094", "T2095", "T2096", "T2130", "T2131")
        if single_panel:
            mask = alpha & (xx > 0.19) & (xx < 0.81) & (yy > 0.19) & (yy < 0.81)
        if id_ == "M0069":
            mask &= (
                (yy > 0.72)
                & (yy < 0.92)
                & (((xx > 0.04) & (xx < 0.17)) | ((xx > 0.82) & (xx < 0.95)))
            )
        if id_ in ("T4801", "T4802"):
            # Pure-red sprite backing is not a plume lamp. Follow the flame's
            # graded pixels and use one moving source per approved hue.
            mask &= g > 0.035
        if rule.get("outer_rings_only"):
            if page == 7 and colors == ["purple", "blue"]:
                target = (
                    (rad > 0.31) & (rad < 0.425)
                    if color == "purple"
                    else (rad >= 0.425) & (rad < 0.48)
                )
            else:
                target = (
                    (rad > 0.41) & (rad < 0.465) & ((yy < 0.5) if color == "blue" else (yy >= 0.5))
                )
            mask = target & alpha
            inferred.append(
                "Ring geometry follows visible circular outline; color assignment requires preview review."
            )
        if rule.get("center_only"):
            mask &= rad < 0.18
        if page == 35:
            # Place the approved palette in concentric regions of the flare,
            # avoiding its unused transparent RGB/background.
            bands = {
                "white": rad < 0.16,
                "yellow": (rad >= 0.16) & (rad < 0.30),
                "purple": (rad >= 0.30) & (rad < 0.43),
                "blue": (rad >= 0.43) & (rad < 0.49),
            }
            if colors == ["purple", "blue"]:
                bands = {
                    "purple": (rad > 0.31) & (rad < 0.425),
                    "blue": (rad >= 0.425) & (rad < 0.48),
                }
            mask = bands.get(color, rad < 0.4) & alpha
            inferred.append(
                "Approved flare colors distributed across center/rings; draft placement."
            )
        if page == 38 and color == "purple" and id_ in ("T4102", "T4103"):
            mask = alpha & (xx > 0.32) & (xx < 0.50) & (yy > 0.15) & (yy < 0.70) & (lum > 0.6)
            inferred.append(
                "Purple tint proposed on existing aurora ribbon; atmospheric emission only."
            )
        if page == 37:
            mask &= (
                (xx > 0.1)
                & (xx < 0.9)
                & (
                    ((yy > 0.02) & (yy < 0.24))
                    if id_ in ("T4087", "T4088")
                    else ((yy > 0.4) & (yy < 0.72))
                )
            )
            inferred.append(
                "One warm source on the broad lit band; checker-plate tread is not a grid of bulbs."
            )
        if not mask.any():
            inferred.append("No confident source region for " + color + "; needs manual placement.")
            continue
        emission[mask, :3] = np.rint(np.array(tint) * 255).astype("uint8")
        emission[mask, 3] = a[:, :, 3][mask]
        # Rings need multiple local centers rather than a lamp at the empty center.
        if rule.get("outer_rings_only") or (page == 35 and color != "white"):
            groups = []
            for section in range(8):
                angle = (np.arctan2(yy - 0.5, xx - 0.5) + 2 * np.pi) % (2 * np.pi)
                part = mask & (angle >= section * np.pi / 4) & (angle < (section + 1) * np.pi / 4)
                if part.any():
                    ys, xs = np.nonzero(part)
                    groups.append(
                        (
                            len(xs),
                            int(xs.min()),
                            int(ys.min()),
                            int(xs.max() + 1),
                            int(ys.max() + 1),
                            float(xs.mean()),
                            float(ys.mean()),
                        )
                    )
        elif single_panel or rule.get("center_only") or page == 37 or id_ in ("T4801", "T4802"):
            ys, xs = np.nonzero(mask)
            groups = [
                (
                    len(xs),
                    int(xs.min()),
                    int(ys.min()),
                    int(xs.max() + 1),
                    int(ys.max() + 1),
                    float(xs.mean()),
                    float(ys.mean()),
                )
            ]
        else:
            groups = components(mask)
            if "missle_turret06" in names:
                groups = groups[:1]
            if id_ == "M0069":
                groups = groups[:2]
        for area, x0, y0, x1, y1, cx, cy in groups[:64]:
            if area < max(3, int(w * h * 0.00001)):
                continue
            points.append(
                dict(
                    color=color,
                    rgb=[round(float(v), 4) for v in tint],
                    uv=[round((cx + 0.5) / w, 6), round((cy + 0.5) / h, 6)],
                    uv_bounds=[
                        round(x0 / w, 6),
                        round(y0 / h, 6),
                        round(x1 / w, 6),
                        round(y1 / h, 6),
                    ],
                    radius_m=0.65 if page in (4, 5) else 1.25 if color in ("red", "green") else 2.0,
                    intensity=0.8,
                    area_pixels=area,
                )
            )
    return im, Image.fromarray(emission), points, sorted(set(inferred))


def prepare(config, out):
    if out.exists():
        raise ValueError("Choose fresh output; retain prior drafts")
    out.mkdir(parents=True)
    (out / "masks").mkdir()
    (out / "previews").mkdir()
    rules = json.loads(config.read_text())
    audit_path = ROOT / rules["audit"]
    audit = json.loads(audit_path.read_text())
    by = {r["id"]: r for r in audit["rows"]}
    pdf = ROOT / rules["review_pdf"]
    reader = PdfReader(pdf)
    assert len(reader.pages) == 40
    decisions = []
    page_ids = {}
    page_previews = []
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    bold = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 19)
    for page, pg in enumerate(reader.pages, 1):
        ids = re.findall(r"\b[TM]\d{4}\b", pg.extract_text())
        assert len(ids) == len(set(ids)) and len(ids) <= 6
        page_ids[str(page)] = ids
        rule = rules["pages"][str(page)]
        assert not set(rule.get("ids", {})) - set(ids), f"Page {page}: explicit ID not on page"
        board = Image.new("RGB", (1200, 1640), (13, 23, 34))
        draw = ImageDraw.Draw(board)
        draw.text(
            (24, 18),
            f"PAGE {page:02d} - LIGHT PLACEMENT DRAFT - NOT IN-GAME",
            font=bold,
            fill="white",
        )
        draw.text(
            (24, 50),
            "Colored marks locate proposed UV regions. Original artwork and current game build are unchanged.",
            font=font,
            fill="#bfd2df",
        )
        if rule.get("assumed"):
            draw.text(
                (24, 76),
                "ASSUMPTION: T0310 centered beacon for page-6 T1641 reference. Please verify.",
                font=font,
                fill="#ffcd76",
            )
        any_approved = False
        for at, id_ in enumerate(ids):
            row = by[id_]
            colors = rule.get("ids", {}).get(id_, rule.get("all", []))
            colors = [] if id_ in rule.get("except", []) else colors
            approved = bool(colors)
            any_approved |= approved
            item = dict(
                id=id_,
                page=page,
                names=row["names"],
                decision="approved" if approved else "no lights",
                colors=colors,
                render_role=role(row),
                original_coverage=row["status"],
                source_pixel_sha256=row["pixel_sha256"],
                runtime_keys=row["runtime_keys"],
                assumed=bool(rule.get("assumed") and approved),
                placements=[],
                notes=[],
            )
            original = source_image(row, audit)
            if approved:
                original, mask, points, notes = placements(
                    original, colors, rule, page, id_, row["names"]
                )
                item["placements"] = points
                item["notes"] = notes
                maskfile = out / "masks" / f"{id_}.png"
                mask.save(maskfile)
                item["emission_mask"] = str(maskfile.relative_to(out))
                item["mask_sha256"] = hashlib.sha256(maskfile.read_bytes()).hexdigest()
                item["runtime_v_transform"] = "1-v" if id_.startswith("M") else "stored-v"
                if item["render_role"] in ("screen/cockpit glow", "atmospheric glow"):
                    item["world_point_lights"] = False
                else:
                    item["world_point_lights"] = True
            x = 24 + (at % 2) * 588
            y = 116 + (at // 2) * 500
            draw.text((x, y), id_ + "  " + " / ".join(row["names"])[:42], font=bold, fill="white")
            draw.text(
                (x, y + 27),
                item["render_role"] if approved else "NO ADDED LIGHTS APPROVED",
                font=font,
                fill="#9bf4c2" if approved else "#b0b9c5",
            )
            picture = original.convert("RGB")
            picture.thumbnail((530, 380))
            px = x + (550 - picture.width) // 2
            py = y + 59
            board.paste(picture, (px, py))
            pd = ImageDraw.Draw(board)
            for n, point in enumerate(item["placements"]):
                u, v = point["uv"]
                cx = px + round(u * picture.width)
                cy = py + round(v * picture.height)
                color = tuple(round(c * 255) for c in point["rgb"])
                u0, v0, u1, v1 = point["uv_bounds"]
                pd.rectangle(
                    (
                        px + u0 * picture.width,
                        py + v0 * picture.height,
                        px + u1 * picture.width,
                        py + v1 * picture.height,
                    ),
                    outline=color,
                    width=1,
                )
                pd.line((cx - 5, cy, cx + 5, cy), fill=color, width=2)
                pd.line((cx, cy - 5, cx, cy + 5), fill=color, width=2)
            description = (
                ", ".join(colors) + f" | {len(item['placements'])} UV centers"
                if approved
                else "Reviewed exclusion retained; no proposed emission mask."
            )
            draw.text(
                (x, y + 449), description[:66], font=font, fill="#ffc878" if approved else "#b0b9c5"
            )
            if item["assumed"]:
                draw.text((x, y + 472), "CENTERED BEACON ASSUMPTION", font=font, fill="#ffc878")
            decisions.append(item)
        if any_approved:
            file = out / "previews" / f"page-{page:02d}-placements.png"
            board.save(file)
            page_previews.append(str(file))
    assert len(decisions) == 239 and len(set(d["id"] for d in decisions)) == 239
    unresolved = [
        dict(id=d["id"], page=d["page"], notes=d["notes"])
        for d in decisions
        if d["decision"] == "approved" and (not d["placements"] or d["notes"])
    ]
    manifest = dict(
        schema_version=1,
        status="Technical placement drafts for remote verification; not runtime-installed",
        source_review=str(config),
        source_review_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
        pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
        audit_sha256=hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        light_limit=16,
        page_ids=page_ids,
        decisions=decisions,
        preview_files=page_previews,
        unresolved=unresolved,
    )
    (out / "placements.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with (out / "decisions.csv").open("w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(
            [
                "ID",
                "Page",
                "Names",
                "Decision",
                "Colors",
                "Render role",
                "UV centers",
                "Assumption",
                "Notes",
            ]
        )
        for d in decisions:
            wr.writerow(
                [
                    d["id"],
                    d["page"],
                    " / ".join(d["names"]),
                    d["decision"],
                    ",".join(d["colors"]),
                    d["render_role"],
                    len(d["placements"]),
                    d["assumed"],
                    " | ".join(d["notes"]),
                ]
            )
    print(
        json.dumps(
            dict(
                reviewed=len(decisions),
                approved=sum(d["decision"] == "approved" for d in decisions),
                excluded=sum(d["decision"] == "no lights" for d in decisions),
                roles=dict(
                    collections.Counter(
                        d["render_role"] for d in decisions if d["decision"] == "approved"
                    )
                ),
                previews=len(page_previews),
                uv_centers=sum(len(d["placements"]) for d in decisions),
                unresolved=len(unresolved),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--review", type=Path, default=ROOT / "docs/texture-light-review-2026-10-20.json"
    )
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    prepare(a.review, a.output)
