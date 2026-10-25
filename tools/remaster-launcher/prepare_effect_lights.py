"""Identify luminous effects by complete pixels in the active upgraded banks.

Produces a local metadata catalog, never changes game media. Alternate native
16-bit quantizations are explicit full-content keys, not prefix/name matches.
"""

from pathlib import Path
import argparse, hashlib, json, re, struct
import numpy as np
from prepare_world_normals import accelerated_hash


def emitter(name):
    n = name.lower()
    color = (1, 0.42, 0.08)
    kind = 0
    radius = 14
    power = 2
    lifetime = 0.14
    if n in ["beamblue", "beamgrn", "beamred"]:
        kind = 1
        radius = 8
        power = 2
        lifetime = 0.075
    elif n in ["gausmuz", "ppcmuz", "macblst"]:
        kind = 2
        radius = 14
        power = 2.8
        lifetime = 0.09
    elif n == "ppc_trail":
        kind = 3
        radius = 9
        power = 2.2
        lifetime = 0.1
    elif n == "gaustrail":
        kind = 4
        radius = 6
        power = 1.4
        lifetime = 0.09
    elif (
        re.fullmatch(r"(impact|mgun_impact)\d+", n)
        or n.startswith("laser_impact_")
        or n in ["green_exp01", "blue_starburst", "red_starburst"]
    ):
        kind = 5
        radius = 18
        power = 2.6
        lifetime = 0.18
    elif re.fullmatch(r"fire_f\d+|nuke\d+", n):
        kind = 6
        radius = 28 if n.startswith("fire") else 45
        power = 2.5 if n.startswith("fire") else 4
        lifetime = 0.18
    # Smoke, dust, water splashes, waypoints, flares and painted rocket/weapon
    # textures are intentionally not accepted as luminous sources.

    if not kind:
        return None
    if "blue" in n or "ppc" in n:
        color = (0.15, 0.4, 1)
    elif "grn" in n or "green" in n or "gaus" in n:
        color = (0.12, 1, 0.2)
    elif "red" in n:
        color = (1, 0.06, 0.025)
    return kind, radius, power, lifetime, *color


def banks(path):
    data = path.read_bytes()
    if data[:8] != b"MWBANK1\0":
        raise ValueError("Invalid active bank map")
    count = struct.unpack_from("<I", data, 8)[0]
    at = 12
    out = []
    if not 0 < count <= 256:
        raise ValueError("Invalid active bank count")
    for _ in range(count):
        a, b = struct.unpack_from("<II", data, at)
        at += 8
        key = data[at : at + a].decode()
        at += a
        file = Path(data[at : at + b].decode())
        at += b
        if not file.is_file():
            raise ValueError("Missing active bank " + str(file))
        out.append((key, file))
    if at != len(data):
        raise ValueError("Trailing bank-map data")
    return out


def prepare(bank_map, output, hash_library, *, native_variant_power=False):
    if output.exists() or output.with_suffix(".json").exists():
        raise ValueError("Choose a fresh output; preserve previous catalog evidence")
    rows = {}
    sources = []
    aliases = {}
    hashes = {}
    digest = accelerated_hash(hash_library)

    def fnv(data):
        key = hashlib.sha256(data).digest()
        if key not in hashes:
            hashes[key] = digest(data)
        return hashes[key]

    for bank, path in banks(bank_map):
        # Read indices without loading large terrain pixel banks into memory.

        with path.open("rb") as f:
            before = path.stat()
            header = f.read(24)
            count = struct.unpack_from("<I", header, 12)[0]
            if count > 65536:
                raise ValueError("Excess image entries")
            table = f.read(count * 40)
            for i in range(count):
                raw, off, marker = struct.unpack_from("<32sII", table, i * 40)
                name = raw.split(b"\0")[0].decode()
                e = emitter(name)
                if e is None:
                    continue
                f.seek(off)
                desc = f.read(16)
                flags, w, h, res, pal, stretch = struct.unpack("<IHHIHH", desc)
                if (
                    flags not in [3, 5, 11, 35, 37, 43, 107]
                    or res
                    or pal
                    or stretch
                    or marker != 0xFFFFFFFF
                    or not 0 < w <= 4096
                    or not 0 < h <= 4096
                ):
                    raise ValueError("Unsupported luminous material " + name)
                flags &= ~96
                end = (
                    struct.unpack_from("<I", table, (i + 1) * 40 + 32)[0]
                    if i + 1 < count
                    else before.st_size
                )
                if end - off != 16 + w * h * (3 if flags == 11 else 2):
                    raise ValueError("Invalid luminous material span " + name)
                data = f.read(w * h * 2)
                words = np.frombuffer(data, dtype="<u2").astype(np.uint32)
                if len(words) != w * h:
                    raise ValueError("Truncated effect image")
                alpha = (
                    np.frombuffer(f.read(w * h), np.uint8).astype(np.uint32)
                    if flags == 11
                    else (
                        np.where(words != 0, 255, 0).astype(np.uint32)
                        if flags == 3
                        else np.full(w * h, 255, np.uint32)
                    )
                )
                if len(alpha) != w * h:
                    raise ValueError("Truncated effect alpha")
                variants = {(1, data)}
                r = (words >> 11) & 31
                g = (words >> 5) & 63
                b = words & 31
                # The late impact frames are smoke. Their faint pixels must
                # not carry the full power of the initial bright flash.

                if e[0] == 5 and not native_variant_power:
                    brightness = np.maximum.reduce([r / 31, g / 63, b / 31]) * alpha / 255
                    visible = brightness[alpha >= 128]
                    level = float(np.quantile(visible, 0.95)) if visible.size else 0
                    e = (*e[:2], e[2] * level * level, *e[3:])
                for rounded in [False, True]:
                    conv = lambda x, a, c: (x * c + a // 2) // a if rounded else x * c // a
                    # Native upload may select a 1-bit or 4-bit alpha format.

                    v1555 = (
                        ((alpha >= 128).astype(np.uint32) << 15)
                        | (r << 10)
                        | (conv(g, 63, 31) << 5)
                        | b
                    )
                    v4444 = (
                        (conv(alpha, 255, 15) << 12)
                        | (conv(r, 31, 15) << 8)
                        | (conv(g, 63, 15) << 4)
                        | conv(b, 31, 15)
                    )
                    variants.add((2, v1555.astype("<u2").tobytes()))
                    variants.add((3, v4444.astype("<u2").tobytes()))
                # The original upload also uses bit truncation; scaling to
                # 15/31 is not identical to dropping the low source bits.

                v1555 = ((alpha >= 128).astype(np.uint32) << 15) | (r << 10) | ((g >> 1) << 5) | b
                v4444 = ((alpha >> 4) << 12) | ((r >> 1) << 8) | ((g >> 2) << 4) | (b >> 1)
                variants.add((2, v1555.astype("<u2").tobytes()))
                variants.add((3, v4444.astype("<u2").tobytes()))
                # Native alpha uploads canonicalize fully transparent texels
                # to zero; their unused RGB differs from bank artwork.

                for fmt, pixels in tuple(variants):
                    if fmt not in (2, 3):
                        continue
                    native = np.frombuffer(pixels, "<u2").copy()
                    # Test original 8-bit alpha, before quantization. Values
                    # 1..15 retain RGB even when the packed alpha nibble is 0.

                    native[alpha == 0] = 0
                    variants.add((fmt, native.tobytes()))
                for fmt, pixels in variants:
                    if fmt in (2, 3) and not np.any(
                        np.frombuffer(pixels, "<u2") & (0x8000 if fmt == 2 else 0xF000)
                    ):
                        continue
                    key = (w, h, fmt, fnv(pixels))
                    value = e
                    if e[0] == 5 and native_variant_power:
                        # Original banks can quantize two impact frames to the
                        # same native pixels. Derive their response from those
                        # exact keyed pixels, rather than their different source
                        # precision. Other emitter ambiguities still fail below.
                        packed = np.frombuffer(pixels, '<u2').astype(np.uint32)
                        if fmt == 1:
                            brightness = np.maximum.reduce([(packed >> 11)/31,
                                ((packed >> 5)&63)/63, (packed&31)/31])
                            alpha_native = np.where(packed != 0, 1., 0.)
                        elif fmt == 2:
                            brightness = np.maximum.reduce([((packed >> 10)&31)/31,
                                ((packed >> 5)&31)/31, (packed&31)/31])
                            alpha_native = (packed >> 15).astype(float)
                        else:
                            brightness = np.maximum.reduce([((packed >> 8)&15)/15,
                                ((packed >> 4)&15)/15, (packed&15)/15])
                            alpha_native = (packed >> 12)/15
                        visible = (brightness*alpha_native)[alpha_native >= .5]
                        level = float(np.quantile(visible,.95)) if visible.size else 0
                        value = (*e[:2],e[2]*level*level,*e[3:])
                    if key in rows and rows[key] != value:
                        # Shared exact pixels do not establish a unique emitter.

                        raise ValueError(
                            "Ambiguous luminous material identity: "
                            + name
                            + " / "
                            + str(aliases[key])
                        )
                    rows[key] = value
                    aliases.setdefault(key, set()).add(name)
                sources.append(
                    dict(
                        bank=bank,
                        path=str(path),
                        entry=i,
                        name=name,
                        pixel_sha256=hashlib.sha256(
                            data + alpha.astype("uint8").tobytes()
                        ).hexdigest(),
                    )
                )
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError("Active bank changed during preparation")
    if not rows or len(rows) > 8192:
        raise ValueError("Empty/excess luminous catalog")
    data = bytearray(b"MWFX1\0\0\0" + struct.pack("<I", len(rows)))
    for (w, h, fmt, digest), e in sorted(rows.items()):
        kind, radius, power, life, *color = e
        data += struct.pack("<IIIIQ6f", w, h, fmt, kind, digest, radius, power, life, *color)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    output.with_suffix(".json").write_text(
        json.dumps(
            dict(
                bank_map=str(bank_map),
                catalog_sha256=hashlib.sha256(data).hexdigest(),
                entries=len(rows),
                sources=sources,
                aliases=[
                    dict(width=k[0], height=k[1], format=k[2], hash=k[3], names=sorted(v))
                    for k, v in sorted(aliases.items())
                ],
            ),
            indent=2,
        )
    )
    print(
        "Effect-light catalog:",
        len(rows),
        "full-content keys from",
        len(sources),
        "active-bank entries",
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--banks", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--native-variant-power", action="store_true",
                   help="Derive impact intensity from exact native pixels (original-bank catalogues)")
    p.add_argument(
        "--hash-library",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "build/default/mw34_normal_hash.dll",
    )
    a = p.parse_args()
    prepare(a.banks, a.output, a.hash_library, native_variant_power=a.native_variant_power)
